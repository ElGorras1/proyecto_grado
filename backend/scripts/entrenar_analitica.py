"""Entrenamiento local explícito, atribuido al sistema, sin simular usuario humano."""

import argparse
import json
from uuid import uuid4

from sqlalchemy import text

from app.db.session import SessionLocal, engine
from app.models.auditoria_historica import ModeloHistorico
from app.schemas.analitica import EntrenamientoHistorico
from app.services.datos_analitica import huella, leer_corte
from app.services.trabajador_analitica import LOCK_ID, ejecutar, evento, recuperar_interrumpidos


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--porcentaje-revision", type=float, default=5)
    args = parser.parse_args()
    config = EntrenamientoHistorico(porcentaje_revision=args.porcentaje_revision)
    with engine.connect() as lock:
        adquirido = lock.scalar(text("SELECT pg_try_advisory_lock(:id)"), {"id": LOCK_ID})
        if not adquirido:
            raise RuntimeError("Hay un trabajador activo; reintenta cuando termine.")
        try:
            with SessionLocal() as db:
                recuperar_interrumpidos(db)
                if db.query(ModeloHistorico).filter_by(plaza=1).first():
                    raise RuntimeError("Ya hay un trabajo pendiente.")
                corte = leer_corte(db, config.excluir_articulos)
                j = ModeloHistorico(
                    id=str(uuid4()),
                    estado="PENDIENTE",
                    plaza=1,
                    usuario_id=None,
                    configuracion=config.model_dump(),
                    corte=corte,
                    huella=huella(corte["filas"]),
                )
                db.add(j)
                evento(
                    db,
                    None,
                    "ANALITICA_SOLICITADA",
                    j.id,
                    {"origen": "CLI_LOCAL_EXPLICITA", "configuracion": j.configuracion},
                )
                db.commit()
                ejecutar(db, j.id)
                print(
                    json.dumps(
                        {"id": j.id, "estado": j.estado, "error": j.error, "metricas": j.metricas},
                        ensure_ascii=False,
                    )
                )
                if j.estado != "COMPLETADO":
                    raise SystemExit(1)
        finally:
            lock.execute(text("SELECT pg_advisory_unlock(:id)"), {"id": LOCK_ID})


if __name__ == "__main__":
    main()
