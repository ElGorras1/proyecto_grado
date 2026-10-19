"""Instala el baseline congelado n49 SOLO cuando no hay tablas públicas."""

from pathlib import Path

from sqlalchemy import inspect, text

from app.db.session import engine

BASELINE = Path(__file__).resolve().parents[1] / "migrations" / "esquema_n49.sql"


def main():
    if engine.url.get_backend_name() != "postgresql":
        raise RuntimeError("La inicialización requiere PostgreSQL")
    with engine.begin() as conn:
        # El lock evita dos inicializadores del mismo servidor en paralelo.
        conn.execute(text("SELECT pg_advisory_xact_lock(681940264)"))
        if inspect(conn).get_table_names(schema="public"):
            raise RuntimeError("La base contiene tablas: no se cambia ni reemplaza su esquema")
        conn.exec_driver_sql(BASELINE.read_text(encoding="utf-8"))
        conn.execute(
            text("INSERT INTO public.alembic_version(version_num) VALUES ('n49e15fa0d73')")
        )
    print(
        "Esquema vacío inicializado en n49e15fa0d73. "
        "Cuentas y catálogo deben configurarse explícitamente."
    )


if __name__ == "__main__":
    main()
