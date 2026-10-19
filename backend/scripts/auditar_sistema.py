"""Diagnóstico PostgreSQL de solo lectura. python -m scripts.auditar_sistema --salida RUTA.json"""
import argparse
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.db.session import engine
from app.models.inventario import AperturaInventario
from app.models.kardex import MovimientoKardex
from app.schemas.kardex import MovimientoKardexOut
from app.services.datos_analitica import leer_corte
from app.services.inventario import verificar_distribucion
from app.services.tratamiento_hil import resumen_tratamiento
from scripts.aplicar_revision_hil import fuente_hash
from scripts.preparar_analitica import digest_tablas


def auditar(conexion_engine=engine):
    if conexion_engine.dialect.name != "postgresql":
        raise RuntimeError("Este diagnóstico de integridad requiere PostgreSQL")
    with conexion_engine.connect().execution_options(isolation_level="REPEATABLE READ") as conn:
        conn.execute(text("SET TRANSACTION READ ONLY"))
        conn.execute(text("SET LOCAL statement_timeout = '60s'"))
        inspector = inspect(conn)
        tablas = inspector.get_table_names()
        huerfanos = []
        indices = {}
        quote = conn.dialect.identifier_preparer.quote
        for tabla in tablas:
            indices[tabla] = [i["name"] for i in inspector.get_indexes(tabla)]
            for fk in inspector.get_foreign_keys(tabla):
                columnas = fk["constrained_columns"]
                referencias = fk["referred_columns"]
                relacion = " AND ".join(
                    f"c.{quote(c)} = p.{quote(p)}" for c, p in zip(columnas, referencias)
                )
                presentes = " AND ".join(f"c.{quote(c)} IS NOT NULL" for c in columnas)
                n = conn.execute(text(
                    f"SELECT count(*) FROM {quote(tabla)} c LEFT JOIN {quote(fk['referred_table'])} p "
                    f"ON {relacion} WHERE {presentes} AND p.{quote(referencias[0])} IS NULL"
                )).scalar_one()
                if n:
                    huerfanos.append({"tabla": tabla, "fk": fk["name"], "filas": n})
        duplicados = conn.execute(text("""
            SELECT count(*) FROM (
                SELECT articulo_id, lote_id, numero_pagina, orden_fila
                FROM movimientos_kardex WHERE estado='ACTIVO' AND lote_id IS NOT NULL
                AND numero_pagina IS NOT NULL AND orden_fila IS NOT NULL
                GROUP BY articulo_id, lote_id, numero_pagina, orden_fila HAVING count(*) > 1
            ) repetidos
        """)).scalar_one()
        with Session(bind=conn) as db:
            corte = leer_corte(db)
            estados = Counter()
            bytes_db = bytes_listado = 0
            for m in db.query(MovimientoKardex).filter(MovimientoKardex.lote_id.isnot(None)):
                tratamiento = resumen_tratamiento(m)
                estados[tratamiento["estado"]] += 1
                bytes_db += len(json.dumps(m.revision_documental, ensure_ascii=False).encode())
                bytes_listado += len(json.dumps(
                    MovimientoKardexOut.model_validate(m).model_dump()["revision_documental"],
                    ensure_ascii=False,
                ).encode())
            inconsistencias = []
            aperturas = db.query(AperturaInventario).all()
            for apertura in aperturas:
                try:
                    verificar_distribucion(db, apertura)
                except RuntimeError as exc:
                    inconsistencias.append({"articulo_id": apertura.articulo_id, "motivo": str(exc)})
            fuente = fuente_hash(db)
        return {
            "generado_en": datetime.now(UTC).isoformat(),
            "solo_lectura": True,
            "revision": conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one(),
            "digest_tablas": digest_tablas(conn, tablas),
            "indices": indices, "huerfanos": huerfanos,
            "posiciones_historicas_duplicadas": duplicados,
            "fuente_sha256": fuente, "perfil_analitico": corte["perfil"],
            "tratamientos_hil": dict(estados),
            "aperturas_comprobadas": len(aperturas),
            "distribuciones_inconsistentes": inconsistencias,
            "revision_documental_bytes": {"almacenados": bytes_db, "listado": bytes_listado},
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--salida", type=Path, required=True)
    args = parser.parse_args()
    resultado = auditar()
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    args.salida.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: resultado[k] for k in (
        "revision", "huerfanos", "posiciones_historicas_duplicadas", "aperturas_comprobadas",
        "distribuciones_inconsistentes", "tratamientos_hil", "revision_documental_bytes",
    )}, ensure_ascii=False))


if __name__ == "__main__":
    main()
