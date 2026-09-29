"""Copia recuperable de las filas afectadas por la migración de calidad HIL."""
import gzip
import json
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy import text
from app.db.session import engine


def main():
    destino = Path("backups") / f"pre_calidad_hil_{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}.json.gz"
    destino.parent.mkdir(exist_ok=True)
    with engine.connect() as conn:
        conn.execute(text("SET TRANSACTION READ ONLY"))
        filas = [dict(r) for r in conn.execute(text("SELECT * FROM movimientos_kardex ORDER BY id")).mappings()]
        version = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
    with gzip.open(destino, "wt", encoding="utf-8") as archivo:
        json.dump({"alembic_version": version, "movimientos_kardex": filas}, archivo, ensure_ascii=False, default=str)
    with gzip.open(destino, "rt", encoding="utf-8") as archivo:
        assert len(json.load(archivo)["movimientos_kardex"]) == len(filas)
    print(f"Respaldo verificado: {destino.resolve()} ({len(filas)} movimientos)")


if __name__ == "__main__":
    main()
