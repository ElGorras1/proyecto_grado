"""Identifica el intento de OCR para recuperar cargas tras reiniciar la API."""
from alembic import op
import sqlalchemy as sa

revision = "c13e8b4d7f02"
down_revision = "b02d7a3c6e91"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("solicitudes_carga_kardex", sa.Column(
        "intento", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("solicitudes_carga_kardex", sa.Column(
        "servidor_instancia", sa.String(36)))
    op.create_check_constraint("ck_solicitud_intento_positivo",
                               "solicitudes_carga_kardex", "intento >= 1")


def downgrade():
    op.drop_constraint("ck_solicitud_intento_positivo", "solicitudes_carga_kardex")
    op.drop_column("solicitudes_carga_kardex", "servidor_instancia")
    op.drop_column("solicitudes_carga_kardex", "intento")
