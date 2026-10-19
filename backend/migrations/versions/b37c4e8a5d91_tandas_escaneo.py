"""Procedencia de escaneos: existentes en tanda 1; futuras cargas en tanda 2."""
from alembic import op
import sqlalchemy as sa
revision = "b37c4e8a5d91"
down_revision = "a26b3d7f4c80"
branch_labels = None
depends_on = None


def upgrade():
    for tabla, nombre in (("lotes_carga", "ck_lote_tanda"), ("solicitudes_carga_kardex", "ck_solicitud_tanda")):
        # PostgreSQL aplica 1 a las filas existentes; se cambia a 2 solo el default futuro.
        op.add_column(tabla, sa.Column("tanda", sa.Integer(), nullable=False, server_default="1"))
        op.alter_column(tabla, "tanda", server_default="2")
        op.create_check_constraint(nombre, tabla, "tanda IN (1, 2)")


def downgrade():
    for tabla, nombre in (("solicitudes_carga_kardex", "ck_solicitud_tanda"), ("lotes_carga", "ck_lote_tanda")):
        op.drop_constraint(nombre, tabla, type_="check")
        op.drop_column(tabla, "tanda")
