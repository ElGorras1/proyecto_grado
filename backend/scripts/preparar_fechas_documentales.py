"""N01: ensayo restaurado, migración y normalización focalizada con reconciliación.

No reentrena, no normaliza fechas por frecuencia y no modifica cantidades.
"""

import argparse
from copy import deepcopy
from datetime import UTC, datetime
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session

from app.db.session import engine
from app.models.kardex import MovimientoKardex
from app.models.auditoria import AuditoriaSistema
from app.services.calidad_kardex import tipos_alerta
from app.services.revision_documental import snapshot_revision
from app.services.tratamiento_hil import huella_datos, resumen_tratamiento
from scripts.respaldo_recuperacion import verificar_paquete, secuencias

BACKEND = Path(__file__).resolve().parents[1]
ANTERIOR = "q72c31ed9f46"
NUEVA = "r83d42fea057"
NUEVOS = ("fecha_documental_texto", "fecha_precision")
MIGRACION = importlib.import_module("migrations.versions.r83d42fea057_fechas_documentales")


def guardar(p, datos):
    p.write_text(json.dumps(datos, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def version(c):
    return c.scalar(text("SELECT version_num FROM alembic_version"))


def estado(c, *, focal=False, auditoria_hasta=None):
    resultado = {}
    for tabla in inspect(c).get_table_names():
        if tabla == "alembic_version":
            continue
        quoted = c.dialect.identifier_preparer.quote(tabla)
        expresion = "to_jsonb(t)"
        filtro = ""
        if tabla == "movimientos_kardex":
            expresion += " - 'fecha_documental_texto' - 'fecha_precision'"
            if focal:
                filtro = " WHERE t.id<>12272"
        if tabla == "auditoria_sistema" and auditoria_hasta is not None:
            filtro = " WHERE t.id<=" + str(int(auditoria_hasta))
        filas = c.scalars(text(f"SELECT ({expresion})::text FROM {quoted} t{filtro}")).all()
        resultado[tabla] = {
            "filas": len(filas),
            "sha256": hashlib.sha256("\n".join(sorted(filas)).encode()).hexdigest(),
        }
    return resultado


def migrar_qa(qa, destino):
    env = os.environ.copy()
    env["DATABASE_URL"] = qa.url.render_as_string(hide_password=False)
    accion = "upgrade" if destino == NUEVA else "downgrade"
    p = subprocess.run(
        [sys.executable, "-m", "alembic", accion, destino],
        cwd=BACKEND,
        env=env,
        capture_output=True,
        text=True,
    )
    if p.returncode:
        raise RuntimeError("Falló el ensayo Alembic: " + p.stderr[-3000:])


def normalizar_fila(db, sha_foto):
    m = db.get(MovimientoKardex, 12272)
    if m.fecha_precision == "AUSENTE" and m.fecha_movimiento is None:
        assert resumen_tratamiento(m)["estado"] == "CATEGORIZADO_CON_MARCA"
        return None
    assert m.articulo_id == 395 and m.lote_id == 414 and m.numero_pagina == 3 and m.orden_fila == 1
    assert m.fecha_movimiento.isoformat() == "2023-01-01" and m.fecha_estado == "ESTIMADA_HIL"
    assert m.revision_documental["fecha_documental"] is None
    assert "FECHA vacía" in m.revision_documental["motivo"]
    previo = snapshot_revision(m)
    revision = deepcopy(m.revision_documental)
    revision.update(
        revision_previa_n01=deepcopy(m.revision_documental),
        fecha_documental=None,
        fecha_precision="AUSENTE",
        origen_fecha="FOTO",
        motivo_fecha="La celda FECHA está vacía. La fecha técnica anterior se conserva en la primera lectura y la auditoría.",
        tarea="N01",
        evidencia_sha256_n01=sha_foto,
    )
    m.fecha_movimiento = None
    m.fecha_precision = "AUSENTE"
    m.fecha_documental_texto = None
    m.fecha_estado = "SIN_FECHA_DOCUMENTAL"
    m.tiene_error_fecha = True
    m.revision_documental = revision
    assert tipos_alerta(m) == ["fecha"]
    registro = {
        "version": 1,
        "avisos": ["fecha"],
        "huella_datos": huella_datos(m),
        "autor": "Codex, por instrucción del titular de completar N01",
        "categorizado_en": datetime.now(UTC).isoformat(),
        "decisiones": [
            {
                "campo": "fecha",
                "categoria": "DATO_AUSENTE",
                "criterios": ["T09", "N01"],
                "motivo": "La fotografía cotejada tiene vacía la fecha del primer ingreso. No se asigna día ni año del hecho.",
            }
        ],
    }
    m.revision_documental = {**revision, "tratamiento_hil": registro}
    nuevo = snapshot_revision(m)
    permitidos = {
        "fecha_movimiento",
        "fecha_precision",
        "fecha_documental_texto",
        "fecha_estado",
        "tiene_error_fecha",
        "revision_documental",
    }
    assert {k: v for k, v in previo.items() if k not in permitidos} == {
        k: v for k, v in nuevo.items() if k not in permitidos
    }
    assert resumen_tratamiento(m)["estado"] == "CATEGORIZADO_CON_MARCA"
    db.add(
        AuditoriaSistema(
            usuario_id=None,
            accion="corregir_kardex_hil",
            recurso="movimientos_kardex",
            recurso_id=m.id,
            resultado="exito",
            fecha_hora=datetime.now(UTC),
            detalle={
                "tarea": "N01",
                "autor_registro": registro["autor"],
                "previo": previo,
                "nuevo": nuevo,
                "motivo": registro["decisiones"][0]["motivo"],
                "evidencia_sha256": sha_foto,
            },
        )
    )
    db.flush()
    return {"movimiento_id": m.id, "previo": previo, "nuevo": nuevo}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--respaldo", type=Path, required=True)
    p.add_argument("--aplicar", action="store_true")
    args = p.parse_args()
    respaldo = args.respaldo.resolve(strict=True)
    if not respaldo.is_relative_to((BACKEND / "backups").resolve()):
        raise RuntimeError("Respaldo fuera de la carpeta autorizada")
    verificar_paquete(respaldo)
    verificacion = json.loads((respaldo / "verificacion.json").read_text(encoding="utf-8"))
    nombre = verificacion["base_restaurada"]
    if verificacion["resultado"] != "VERIFICADO" or not re.fullmatch(
        r"activos_recuperacion_qa_[a-z0-9]+", nombre
    ):
        raise RuntimeError("Falta la restauración QA verificada")
    out = BACKEND / "backups" / "n01_fechas_20261028"
    out.mkdir(exist_ok=True)
    foto = BACKEND / "storage/kardex_images/lote_408107fb_pag_3.webp"
    sha_foto = hashlib.sha256(foto.read_bytes()).hexdigest()
    qa = create_engine(engine.url.set(database=nombre))
    with qa.connect() as c:
        v = version(c)
        original = estado(c)
        seq = secuencias(c)
    if v == NUEVA:
        migrar_qa(qa, ANTERIOR)
    elif v != ANTERIOR:
        raise RuntimeError("La copia QA tiene otra revisión")
    migrar_qa(qa, NUEVA)
    with qa.connect() as c:
        assert estado(c) == original and secuencias(c) == seq
        with Session(bind=c) as db:
            cambio = normalizar_fila(db, sha_foto)
            assert cambio
            with Operations.context(MigrationContext.configure(c)):
                try:
                    MIGRACION.downgrade()
                except RuntimeError:
                    pass
                else:
                    raise AssertionError("La reversión permitió perder una fecha/documento nuevo")
            db.rollback()
    migrar_qa(qa, ANTERIOR)
    with qa.connect() as c:
        assert estado(c) == original
    migrar_qa(qa, NUEVA)
    # La secuencia de auditoría se consumió en la transacción QA revertida; no se compara con producción.
    with qa.connect() as c:
        assert estado(c) == original
    reporte = {
        "tarea": "N01",
        "respaldo": str(respaldo),
        "base_ensayo": nombre,
        "migracion": NUEVA,
        "ensayo_upgrade_downgrade_upgrade": "APROBADO",
        "filas_previas_inalteradas": True,
        "reversion_con_datos_nuevos": "BLOQUEADA",
        "foto_sha256": sha_foto,
        "aplicado": False,
    }
    guardar(out / "ensayo_migracion.json", reporte)
    if args.aplicar:
        with engine.begin() as c:
            c.execute(text("SET LOCAL lock_timeout='5s'"))
            c.execute(text("SET LOCAL statement_timeout='60s'"))
            tablas = inspect(c).get_table_names()
            c.execute(
                text(
                    "LOCK TABLE "
                    + ", ".join(c.dialect.identifier_preparer.quote(t) for t in sorted(tablas))
                    + " IN SHARE ROW EXCLUSIVE MODE"
                )
            )
            assert version(c) == ANTERIOR, "La instalación ya cambió de revisión"
            assert estado(c) == original, "La base cambió desde el respaldo ensayado"
            sec_antes = secuencias(c)
            max_aud = c.scalar(text("SELECT coalesce(max(id),0) FROM auditoria_sistema"))
            antes = estado(c, focal=True, auditoria_hasta=max_aud)
            with Operations.context(MigrationContext.configure(c)):
                MIGRACION.upgrade()
            assert estado(c) == original and secuencias(c) == sec_antes
            c.execute(text("UPDATE alembic_version SET version_num=:n"), {"n": NUEVA})
            with Session(bind=c) as db:
                cambio = normalizar_fila(db, sha_foto)
                assert cambio
                assert estado(c, focal=True, auditoria_hasta=max_aud) == antes
                assert (
                    c.scalar(
                        text("SELECT count(*) FROM auditoria_sistema WHERE id>:m"), {"m": max_aud}
                    )
                    == 1
                )
                guardar(out / "cambio_focalizado.json", cambio)
        reporte.update(aplicado=True, unico_movimiento_modificado=12272, auditorias_nuevas=1)
        guardar(out / "resultado_aplicacion.json", reporte)
    qa.dispose()
    print(json.dumps(reporte, ensure_ascii=False))


if __name__ == "__main__":
    main()
