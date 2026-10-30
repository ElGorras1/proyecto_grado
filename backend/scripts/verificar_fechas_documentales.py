"""Comprobación N01 sobre copia restaurada o instalación real de solo lectura."""

import argparse
import asyncio
from collections import Counter
import hashlib
import json
from pathlib import Path

import httpx
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.db.session import engine, get_db
from app.main import app
from app.models.kardex import MovimientoKardex
from app.models.auditoria_historica import ModeloHistorico, ResultadoHistorico
from app.services.datos_analitica import leer_corte
from app.services.evaluacion_analitica import diagnosticar
from app.services.tratamiento_hil import resumen_tratamiento
from scripts.preparar_fechas_documentales import normalizar_fila

BACKEND = Path(__file__).resolve().parents[1]


async def verificar(ensayo):
    out = BACKEND / "backups/n01_fechas_20261028"
    cfg = json.loads((out / "ensayo_migracion.json").read_text(encoding="utf-8"))
    db_engine = create_engine(engine.url.set(database=cfg["base_ensayo"])) if ensayo else engine
    reporte = {"tarea": "N01", "modo": "ENSAYO" if ensayo else "SOLO_LECTURA", "consultas": []}
    with db_engine.connect().execution_options(isolation_level="REPEATABLE READ") as conn:
        if not ensayo:
            conn.execute(text("SET TRANSACTION READ ONLY"))
        with Session(bind=conn) as db:
            if ensayo:
                normalizar_fila(db, cfg["foto_sha256"])
            m = db.get(MovimientoKardex, 12272)
            assert m.fecha_movimiento is None and m.fecha_precision == "AUSENTE"
            assert (
                m.fecha_original.isoformat() == "2023-01-01"
                and m.datos_originales["fecha"] == "2023-01-01"
            )
            assert m.ingresos == 5 and m.saldo_registrado == 6
            assert resumen_tratamiento(m)["estado"] == "CATEGORIZADO_CON_MARCA"
            filas = db.query(MovimientoKardex).all()
            reporte["hil"] = dict(
                Counter(
                    resumen_tratamiento(f)["estado"]
                    for f in filas
                    if f.lote_id is not None and f.estado == "ACTIVO"
                )
            )
            assert reporte["hil"].get("CATEGORIZADO_CON_MARCA") == 117
            assert (
                reporte["hil"].get("POR_CATEGORIZAR", 0) == 0
                and reporte["hil"].get("REQUIERE_RECATEGORIZAR", 0) == 0
            )
            corte = leer_corte(db)
            assert corte["perfil"]["total"] == 11918 and corte["perfil"]["elegibles"] == 8367
            assert 12272 in corte["exclusiones"]["fecha_no_documentada"]
            reporte["perfil"] = corte["perfil"]
            modelo = (
                db.query(ModeloHistorico)
                .filter_by(estado="COMPLETADO")
                .order_by(ModeloHistorico.creado_en.desc())
                .first()
            )
            resultados = db.query(ResultadoHistorico).filter_by(modelo_id=modelo.id).all()
            d = diagnosticar(modelo, resultados)
            assert d["estado"] == "CONSISTENTE"
            assert (
                hashlib.sha256(
                    (BACKEND / ".analytics" / f"{modelo.id}.joblib").read_bytes()
                ).hexdigest()
                == modelo.artefacto_sha256
            )
            reporte["modelo"] = {
                "id": modelo.id,
                "estado": d["estado"],
                "resultados": len(resultados),
                "archivo_sin_cambios": True,
            }
            uid = conn.scalar(
                text(
                    "SELECT u.id FROM usuario u JOIN rol r ON r.id=u.rol_id WHERE u.estado='activo' AND r.estado='activo' AND r.nombre='Auditor' ORDER BY u.id LIMIT 1"
                )
            )

            def sesion():
                yield db

            app.dependency_overrides[get_db] = sesion
            try:
                async with httpx.AsyncClient(
                    transport=httpx.ASGITransport(app=app),
                    base_url="http://qa.local",
                    headers={"Authorization": "Bearer " + create_access_token(uid)},
                ) as client:
                    urls = [
                        "/api/v1/kardex/historial/395",
                        "/api/v1/kardex/errores?tipo=fecha",
                        "/api/v1/reportes/inventario",
                        "/api/v1/reportes/inventario?gestion=2023",
                        "/api/v1/reportes/inventario.csv",
                        "/api/v1/reportes/inventario/opciones",
                        "/api/v1/kardex/articulos/395/trazabilidad?ambito=HISTORICO&sin_fecha=true&limite=100",
                        "/api/v1/kardex/articulos/395/trazabilidad?ambito=HISTORICO&desde=2023-01-01&hasta=2023-12-31",
                        "/api/v1/kardex/cobertura/395",
                        "/api/v1/analitica/reglas-historicas?articulo=CD&seleccion=todos",
                        "/api/v1/analitica/reglas-historicas/opciones",
                        "/api/v1/reportes/dashboard?gestion=2026",
                        "/api/v1/analitica/perfil",
                        "/api/v1/analitica/temporal/plan?gestion_evaluacion=2025",
                        "/api/v1/reportes/institucional?gestion=2026",
                    ]
                    for url in urls:
                        r = await client.get(url)
                        assert r.status_code == 200, (url, r.status_code, r.text[:300])
                        reporte["consultas"].append({"url": url, "http": r.status_code})
                        if url == "/api/v1/kardex/historial/395":
                            f = next(f for f in r.json() if f["id"] == 12272)
                            assert (
                                f["fecha_movimiento"] is None and f["fecha_precision"] == "AUSENTE"
                            )
                        if url == "/api/v1/reportes/inventario":
                            assert r.json()["gestion"] is None
                            reporte["sin_gestion_confirmada"] = r.json()["resumen"]["movimientos"]
                        if url.endswith("hasta=2023-12-31"):
                            assert not any(f["id"] == 12272 for f in r.json()["eventos"])
                        if "sin_fecha=true" in url:
                            f = next(f for f in r.json()["eventos"] if f["id"] == 12272)
                            assert f["fecha"] is None
            finally:
                app.dependency_overrides.clear()
            if not ensayo:
                assert conn.scalar(text("SHOW transaction_read_only")) == "on"
            if ensayo:
                db.rollback()
    if ensayo:
        db_engine.dispose()
    (out / ("verificacion_ensayo.json" if ensayo else "verificacion_instalacion.json")).write_text(
        json.dumps(reporte, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        json.dumps({k: v for k, v in reporte.items() if k not in ("perfil",)}, ensure_ascii=False)
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--ensayo", action="store_true")
    args = p.parse_args()
    asyncio.run(verificar(args.ensayo))
