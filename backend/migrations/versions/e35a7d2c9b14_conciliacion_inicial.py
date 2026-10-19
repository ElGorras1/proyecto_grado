"""Corte de conteo fisico y ajuste inicial por articulo."""
from alembic import op
import sqlalchemy as sa

revision = "e35a7d2c9b14"
down_revision = "d24f9c5e8a13"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "conciliacion_inicial",
        sa.Column("articulo_id", sa.Integer(), sa.ForeignKey("activo.id"), primary_key=True),
        sa.Column("cantidad_base", sa.Integer(), nullable=False),
        sa.Column("cantidad_fisica", sa.Integer(), nullable=False),
        sa.Column("diferencia", sa.Integer(), nullable=False),
        sa.Column("fecha_conteo", sa.Date(), nullable=False),
        sa.Column("distribucion_anterior", sa.JSON(), nullable=False),
        sa.Column("areas", sa.JSON(), nullable=False),
        sa.Column("referencia_documento", sa.String(255), nullable=False),
        sa.Column("justificacion", sa.Text(), nullable=False),
        sa.Column("encargado_id", sa.Integer(), sa.ForeignKey("usuario.id"), nullable=False),
        sa.Column("registrado_por", sa.Integer(), sa.ForeignKey("usuario.id"), nullable=False),
        sa.Column("registrado_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("origen_base", sa.String(30), nullable=False),
        sa.Column("movimiento_historico_id", sa.Integer()),
        sa.Column("ajuste_movimiento_id", sa.Integer(), sa.ForeignKey("movimientos_kardex.id")),
        sa.CheckConstraint("cantidad_base >= 0", name="ck_conciliacion_base"),
        sa.CheckConstraint("cantidad_fisica >= 0", name="ck_conciliacion_fisica"),
        sa.CheckConstraint("diferencia = cantidad_fisica - cantidad_base", name="ck_conciliacion_diferencia"),
    )


def downgrade():
    op.drop_table("conciliacion_inicial")
