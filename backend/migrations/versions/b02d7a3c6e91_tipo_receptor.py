"""Distingue persona, institución y público general que recibe una salida."""
from alembic import op
import sqlalchemy as sa

revision = "b02d7a3c6e91"
down_revision = "a91c6e7b2d04"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("movimientos_kardex", sa.Column("receptor_tipo", sa.String(24)))
    op.create_check_constraint("ck_kardex_receptor_tipo", "movimientos_kardex",
                               "receptor_tipo IS NULL OR receptor_tipo IN ('PERSONA', 'INSTITUCION', 'PUBLICO_GENERAL')")


def downgrade():
    op.drop_constraint("ck_kardex_receptor_tipo", "movimientos_kardex")
    op.drop_column("movimientos_kardex", "receptor_tipo")
