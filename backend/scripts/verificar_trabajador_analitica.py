"""QA del trabajador: ejecutar solamente sobre una copia activos_analitica_qa_*."""

import time
from uuid import uuid4

from sqlalchemy import text

from app.db.session import SessionLocal, engine
from app.models.auditoria_historica import ModeloHistorico, ResultadoHistorico
from app.schemas.analitica import EntrenamientoHistorico
from app.services.datos_analitica import huella, leer_corte
from app.services.trabajador_analitica import LOCK_ID, detener, iniciar


def main():
    assert engine.url.database.startswith("activos_analitica_qa_"), "Solo copia QA"
    with engine.connect() as a, engine.connect() as b:
        assert a.scalar(text("SELECT pg_try_advisory_lock(:id)"), {"id": LOCK_ID})
        assert not b.scalar(text("SELECT pg_try_advisory_lock(:id)"), {"id": LOCK_ID})
        a.execute(text("SELECT pg_advisory_unlock(:id)"), {"id": LOCK_ID})
    with SessionLocal() as db:
        corte = leer_corte(db)
        j = ModeloHistorico(
            id=str(uuid4()),
            usuario_id=None,
            estado="PENDIENTE",
            plaza=1,
            configuracion=EntrenamientoHistorico().model_dump(),
            corte=corte,
            huella=huella(corte["filas"]),
        )
        db.add(j)
        db.commit()
        id = j.id
    iniciar()
    try:
        for _ in range(45):
            with SessionLocal() as db:
                j = db.get(ModeloHistorico, id)
                if j.estado not in ("PENDIENTE", "EN_EJECUCION"):
                    assert j.estado == "COMPLETADO", j.error
                    assert (
                        db.query(ResultadoHistorico).filter_by(modelo_id=id).count()
                        == corte["perfil"]["elegibles"]
                    )
                    print("Trabajador: completado. Exclusión mutua entre conexiones: correcta.")
                    break
            time.sleep(1)
        else:
            raise RuntimeError("El trabajador no terminó.")
    finally:
        detener()


if __name__ == "__main__":
    main()
