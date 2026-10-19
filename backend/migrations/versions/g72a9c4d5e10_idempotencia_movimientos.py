"""Identifica solicitudes modernas para evitar movimientos duplicados."""
from alembic import op
import sqlalchemy as sa

revision = "g72a9c4d5e10"
down_revision = "f46b8e3d1a20"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("movimientos_kardex", sa.Column("solicitud_id", sa.String(36)))
    op.add_column("movimientos_kardex", sa.Column("solicitud_huella", sa.String(64)))
    op.create_unique_constraint("uq_movimiento_solicitud", "movimientos_kardex", ["solicitud_id"])


def downgrade():
    op.drop_constraint("uq_movimiento_solicitud", "movimientos_kardex", type_="unique")
    op.drop_column("movimientos_kardex", "solicitud_huella")
    op.drop_column("movimientos_kardex", "solicitud_id")
