"""Identidades separadas del encargado y del usuario registrador."""
from alembic import op
import sqlalchemy as sa


revision = "e72d6c4a1b90"
down_revision = "c48d5e9b6f02"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("movimientos_kardex", sa.Column("encargado_id", sa.Integer()))
    op.add_column("movimientos_kardex", sa.Column("usuario_registrador_id", sa.Integer()))
    op.add_column("movimientos_kardex", sa.Column("encargado_nombre", sa.String(120)))
    op.create_foreign_key("fk_movimiento_encargado", "movimientos_kardex", "usuario",
                          ["encargado_id"], ["id"])
    op.create_foreign_key("fk_movimiento_registrador", "movimientos_kardex", "usuario",
                          ["usuario_registrador_id"], ["id"])


def downgrade():
    op.drop_constraint("fk_movimiento_registrador", "movimientos_kardex", type_="foreignkey")
    op.drop_constraint("fk_movimiento_encargado", "movimientos_kardex", type_="foreignkey")
    op.drop_column("movimientos_kardex", "encargado_nombre")
    op.drop_column("movimientos_kardex", "usuario_registrador_id")
    op.drop_column("movimientos_kardex", "encargado_id")
