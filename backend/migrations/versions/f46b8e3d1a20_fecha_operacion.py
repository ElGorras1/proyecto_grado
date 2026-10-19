"""Separa la fecha y hora de la operación de su registro digital."""
from alembic import op
import sqlalchemy as sa

revision = "f46b8e3d1a20"
down_revision = "e35a7d2c9b14"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("movimientos_kardex", sa.Column(
        "ocurrido_en", sa.DateTime(timezone=True), nullable=True))


def downgrade():
    op.drop_column("movimientos_kardex", "ocurrido_en")
