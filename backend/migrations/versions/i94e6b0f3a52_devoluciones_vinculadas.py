"""Vincula devoluciones operativas con su entrega original."""
from alembic import op
import sqlalchemy as sa

revision = "i94e6b0f3a52"
down_revision = "h83d5a9e7c21"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("movimientos_kardex", sa.Column("movimiento_origen_id", sa.Integer(), nullable=True))
    op.add_column("movimientos_kardex", sa.Column("devuelto_por", sa.String(200), nullable=True))
    op.create_foreign_key("fk_movimiento_devolucion_origen", "movimientos_kardex",
                          "movimientos_kardex", ["movimiento_origen_id"], ["id"])
    op.create_check_constraint("ck_movimiento_devolucion_no_reflexiva", "movimientos_kardex",
                               "movimiento_origen_id IS NULL OR movimiento_origen_id <> id")
    op.create_index("ix_movimiento_devolucion_origen", "movimientos_kardex", ["movimiento_origen_id"])


def downgrade():
    op.drop_index("ix_movimiento_devolucion_origen", table_name="movimientos_kardex")
    op.drop_constraint("ck_movimiento_devolucion_no_reflexiva", "movimientos_kardex", type_="check")
    op.drop_constraint("fk_movimiento_devolucion_origen", "movimientos_kardex", type_="foreignkey")
    op.drop_column("movimientos_kardex", "devuelto_por")
    op.drop_column("movimientos_kardex", "movimiento_origen_id")
