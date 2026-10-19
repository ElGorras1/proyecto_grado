"""Asientos de rectificación sin reescribir operaciones anteriores."""
from alembic import op
import sqlalchemy as sa

revision = "k16a8d2b7c40"
down_revision = "j05f7c1a4b63"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("movimientos_kardex", sa.Column("corrige_movimiento_id", sa.Integer()))
    op.add_column("movimientos_kardex", sa.Column("cantidad_anterior", sa.Integer()))
    op.add_column("movimientos_kardex", sa.Column("cantidad_corregida", sa.Integer()))
    op.add_column("movimientos_kardex", sa.Column("motivo_correccion", sa.Text()))
    op.add_column("movimientos_kardex", sa.Column("autorizado_por_id", sa.Integer()))
    op.create_foreign_key("fk_movimiento_correccion_origen", "movimientos_kardex",
                          "movimientos_kardex", ["corrige_movimiento_id"], ["id"])
    op.create_foreign_key("fk_movimiento_correccion_autorizado", "movimientos_kardex",
                          "usuario", ["autorizado_por_id"], ["id"])
    op.create_check_constraint("ck_movimiento_correccion_cantidades", "movimientos_kardex",
        "(cantidad_anterior IS NULL OR cantidad_anterior >= 0) AND "
        "(cantidad_corregida IS NULL OR cantidad_corregida >= 0) AND "
        "(corrige_movimiento_id IS NULL OR corrige_movimiento_id <> id)")
    op.create_index("ix_movimiento_correccion_origen", "movimientos_kardex",
                    ["corrige_movimiento_id"])


def downgrade():
    op.drop_index("ix_movimiento_correccion_origen", table_name="movimientos_kardex")
    op.drop_constraint("ck_movimiento_correccion_cantidades", "movimientos_kardex", type_="check")
    op.drop_constraint("fk_movimiento_correccion_autorizado", "movimientos_kardex", type_="foreignkey")
    op.drop_constraint("fk_movimiento_correccion_origen", "movimientos_kardex", type_="foreignkey")
    for columna in ("autorizado_por_id", "motivo_correccion", "cantidad_corregida",
                    "cantidad_anterior", "corrige_movimiento_id"):
        op.drop_column("movimientos_kardex", columna)
