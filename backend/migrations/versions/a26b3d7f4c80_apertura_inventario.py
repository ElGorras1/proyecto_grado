"""Apertura explícita: no inferir existencias físicas del Kárdex."""
from alembic import op
import sqlalchemy as sa
revision = "a26b3d7f4c80"
down_revision = "f15a2c6e3b79"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("apertura_inventario",
        sa.Column("articulo_id", sa.Integer(), sa.ForeignKey("activo.id"), primary_key=True),
        sa.Column("cantidad_inicial", sa.Integer(), nullable=False),
        sa.Column("cantidad_actual", sa.Integer(), nullable=False),
        sa.Column("ultimo_moderno_id", sa.Integer(), nullable=False),
        sa.Column("aprobado_por", sa.Integer(), sa.ForeignKey("usuario.id"), nullable=False),
        sa.Column("aprobado_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("referencia_documento", sa.String(255), nullable=False),
        sa.Column("justificacion", sa.Text(), nullable=False),
        sa.CheckConstraint("cantidad_inicial >= 0", name="ck_apertura_inicial"),
        sa.CheckConstraint("cantidad_actual >= 0 AND cantidad_actual <= 2147483647", name="ck_apertura_actual"),
    )

def downgrade():
    op.drop_table("apertura_inventario")
