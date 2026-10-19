"""Conserva los avisos y su justificación en las transferencias operativas."""
from alembic import op
import sqlalchemy as sa

revision = "l27b9c3e8d51"
down_revision = "k16a8d2b7c40"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("transferencia_area", sa.Column("alertas_control", sa.JSON()))
    op.add_column("transferencia_area", sa.Column("justificacion_alertas", sa.Text()))


def downgrade():
    op.drop_column("transferencia_area", "justificacion_alertas")
    op.drop_column("transferencia_area", "alertas_control")
