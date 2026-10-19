"""Permite tandas adicionales sin reclasificar el histórico existente."""

import sqlalchemy as sa

from alembic import op

revision = "o50a19cb7d24"
down_revision = "n49e15fa0d73"
branch_labels = None
depends_on = None

TABLAS = (("lotes_carga", "ck_lote_tanda"), ("solicitudes_carga_kardex", "ck_solicitud_tanda"))


def upgrade():
    for tabla, nombre in TABLAS:
        op.drop_constraint(nombre, tabla, type_="check")
        op.create_check_constraint(nombre, tabla, "tanda BETWEEN 1 AND 9999")


def downgrade():
    conexion = op.get_bind()
    for tabla, _ in TABLAS:
        if conexion.execute(sa.text(f"SELECT count(*) FROM {tabla} WHERE tanda > 2")).scalar_one():
            raise RuntimeError("No se puede retroceder: existen escaneos en tandas posteriores a 2")
    for tabla, nombre in reversed(TABLAS):
        op.drop_constraint(nombre, tabla, type_="check")
        op.create_check_constraint(nombre, tabla, "tanda IN (1, 2)")
