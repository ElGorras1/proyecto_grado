"""Registra transferencias atómicas entre áreas operativas."""
from alembic import op
import sqlalchemy as sa

revision = "h83d5a9e7c21"
down_revision = "g72a9c4d5e10"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "transferencia_area",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("solicitud_id", sa.String(36), nullable=False),
        sa.Column("solicitud_huella", sa.String(64), nullable=False),
        sa.Column("articulo_id", sa.Integer(), sa.ForeignKey("activo.id"), nullable=False),
        sa.Column("area_origen_id", sa.Integer(), sa.ForeignKey("area.id"), nullable=False),
        sa.Column("area_destino_id", sa.Integer(), sa.ForeignKey("area.id"), nullable=False),
        sa.Column("cantidad", sa.Integer(), nullable=False),
        sa.Column("total_institucional", sa.Integer(), nullable=False),
        sa.Column("encargado_id", sa.Integer(), sa.ForeignKey("usuario.id"), nullable=False),
        sa.Column("registrado_por", sa.Integer(), sa.ForeignKey("usuario.id"), nullable=False),
        sa.Column("ocurrido_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("registrado_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("referencia_documento", sa.String(200), nullable=False),
        sa.Column("observaciones", sa.Text(), nullable=False),
        sa.UniqueConstraint("solicitud_id", name="uq_transferencia_solicitud"),
        sa.CheckConstraint("cantidad > 0", name="ck_transferencia_cantidad"),
        sa.CheckConstraint("area_origen_id <> area_destino_id", name="ck_transferencia_areas"),
    )


def downgrade():
    op.drop_table("transferencia_area")
