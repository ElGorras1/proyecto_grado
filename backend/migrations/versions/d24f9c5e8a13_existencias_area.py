"""Distribuye stock por áreas y conserva el saldo de ubicación desconocida."""
from alembic import op
import sqlalchemy as sa

revision = "d24f9c5e8a13"
down_revision = "c13e8b4d7f02"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("apertura_inventario", sa.Column(
        "cantidad_sin_ubicacion", sa.Integer(), nullable=False, server_default="0"))
    op.execute("UPDATE apertura_inventario SET cantidad_sin_ubicacion = cantidad_actual")
    op.create_check_constraint("ck_apertura_sin_ubicacion", "apertura_inventario",
                               "cantidad_sin_ubicacion >= 0")
    op.add_column("movimientos_kardex", sa.Column(
        "area_operativa_id", sa.Integer(), sa.ForeignKey("area.id")))
    # existencia ya trae uq_existencia_activo_area y ck_existencia_cantidad.


def downgrade():
    op.drop_column("movimientos_kardex", "area_operativa_id")
    op.drop_constraint("ck_apertura_sin_ubicacion", "apertura_inventario")
    op.drop_column("apertura_inventario", "cantidad_sin_ubicacion")
