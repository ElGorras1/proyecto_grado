"""Conservar la procedencia del saldo inicial tomado del Kárdex histórico."""
from alembic import op
import sqlalchemy as sa

revision = "c48d5e9b6f02"
down_revision = "b37c4e8a5d91"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("apertura_inventario", sa.Column(
        "origen", sa.String(30), nullable=False, server_default="CONTEO_FISICO"))
    op.add_column("apertura_inventario", sa.Column("movimiento_historico_id", sa.Integer()))
    op.add_column("apertura_inventario", sa.Column("lote_historico_id", sa.Integer()))
    op.create_check_constraint("ck_apertura_origen", "apertura_inventario",
                               "origen IN ('CONTEO_FISICO', 'KARDEX_HISTORICO')")


def downgrade():
    op.drop_constraint("ck_apertura_origen", "apertura_inventario", type_="check")
    op.drop_column("apertura_inventario", "lote_historico_id")
    op.drop_column("apertura_inventario", "movimiento_historico_id")
    op.drop_column("apertura_inventario", "origen")
