"""Keep upload fingerprints and reversible duplicate movement archive."""
from alembic import op
import sqlalchemy as sa

revision = "d93f0a4c1e57"
down_revision = "c82e31a90b42"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "solicitudes_carga_kardex",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("articulo_id", sa.Integer(), sa.ForeignKey("activo.id"), nullable=False),
        sa.Column("huella", sa.String(64), nullable=False),
        sa.Column("estado", sa.String(20), nullable=False),
        sa.Column("lote_id", sa.Integer(), sa.ForeignKey("lotes_carga.id")),
        sa.Column("pendiente_id", sa.String(36), sa.ForeignKey("lotes_pendientes.id")),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuario.id")),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("articulo_id", "huella", name="uq_carga_articulo_huella"),
    )
    op.create_table(
        "movimientos_kardex_archivados",
        sa.Column("movimiento_id", sa.Integer(), primary_key=True),
        sa.Column("lote_original_id", sa.Integer(), sa.ForeignKey("lotes_carga.id"), nullable=False),
        sa.Column("lote_canonico_id", sa.Integer(), sa.ForeignKey("lotes_carga.id"), nullable=False),
        sa.Column("datos", sa.JSON(), nullable=False),
        sa.Column("archivado_en", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade():
    op.drop_table("movimientos_kardex_archivados")
    op.drop_table("solicitudes_carga_kardex")
