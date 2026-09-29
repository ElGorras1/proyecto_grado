"""Persist scans awaiting title confirmation."""
from alembic import op
import sqlalchemy as sa

revision = "c82e31a90b42"
down_revision = "b71d2e9f4a63"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "lotes_pendientes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("articulo_id", sa.Integer(), sa.ForeignKey("activo.id"), nullable=False),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuario.id"), nullable=False),
        sa.Column("extraccion", sa.JSON(), nullable=False),
        sa.Column("estado", sa.String(20), nullable=False),
        sa.Column("lote_id", sa.Integer(), sa.ForeignKey("lotes_carga.id")),
    )


def downgrade():
    op.drop_table("lotes_pendientes")
