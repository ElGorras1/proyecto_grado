"""Fecha y alertas determinísticas de movimientos modernos."""
from alembic import op
import sqlalchemy as sa


revision = "f83c9a1e2d47"
down_revision = "e72d6c4a1b90"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("movimientos_kardex", sa.Column("registrado_en", sa.DateTime(timezone=True)))
    op.add_column("movimientos_kardex", sa.Column("alertas_control", sa.JSON()))
    op.add_column("movimientos_kardex", sa.Column("justificacion_alertas", sa.Text()))


def downgrade():
    op.drop_column("movimientos_kardex", "justificacion_alertas")
    op.drop_column("movimientos_kardex", "alertas_control")
    op.drop_column("movimientos_kardex", "registrado_en")
