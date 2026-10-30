"""Compensaciones de transferencias y custodias sin reescribir originales."""
import sqlalchemy as sa
from alembic import op
revision = "u16a75c1d380"
down_revision = "t05f64b0c279"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("custodia_externa", sa.Column("cantidad_ajustada", sa.Integer(), nullable=False, server_default="0"))
    op.drop_constraint("ck_custodia_balance", "custodia_externa", type_="check")
    op.create_check_constraint("ck_custodia_balance", "custodia_externa",
        "cantidad_entregada + cantidad_ajustada = cantidad_fuera + cantidad_vendida + cantidad_devuelta AND cantidad_entregada + cantidad_ajustada BETWEEN 0 AND 2147483647")
    op.create_table("rectificacion_logistica",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("solicitud_id", sa.String(36), nullable=False, unique=True),
        sa.Column("solicitud_huella", sa.String(64), nullable=False),
        sa.Column("articulo_id", sa.Integer(), sa.ForeignKey("activo.id"), nullable=False),
        sa.Column("clase", sa.String(24), nullable=False),
        sa.Column("transferencia_id", sa.Integer(), sa.ForeignKey("transferencia_area.id")),
        sa.Column("custodia_id", sa.Integer(), sa.ForeignKey("custodia_externa.id")),
        sa.Column("evento_custodia_id", sa.Integer(), sa.ForeignKey("evento_custodia_externa.id")),
        sa.Column("anterior_id", sa.Integer(), sa.ForeignKey("rectificacion_logistica.id")),
        sa.Column("previo", sa.JSON(), nullable=False), sa.Column("nuevo", sa.JSON(), nullable=False),
        sa.Column("areas_delta", sa.JSON(), nullable=False),
        sa.Column("delta_total", sa.Integer(), nullable=False),
        sa.Column("delta_custodia", sa.Integer(), nullable=False),
        sa.Column("total_despues", sa.Integer(), nullable=False),
        sa.Column("custodia_despues", sa.Integer(), nullable=False),
        sa.Column("registrado_por", sa.Integer(), sa.ForeignKey("usuario.id"), nullable=False),
        sa.Column("registrado_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("referencia_documento", sa.String(200), nullable=False),
        sa.Column("motivo", sa.Text(), nullable=False),
        sa.CheckConstraint("(clase='TRANSFERENCIA' AND transferencia_id IS NOT NULL AND custodia_id IS NULL AND evento_custodia_id IS NULL) OR (clase='ENTREGA' AND transferencia_id IS NULL AND custodia_id IS NOT NULL AND evento_custodia_id IS NULL) OR (clase='EVENTO_CUSTODIA' AND transferencia_id IS NULL AND custodia_id IS NOT NULL AND evento_custodia_id IS NOT NULL)", name="ck_rectificacion_logistica_origen"),
        sa.CheckConstraint("anterior_id IS NULL OR anterior_id<>id", name="ck_rectificacion_logistica_no_reflexiva"))
    op.create_index("ix_rectificacion_logistica_articulo_id", "rectificacion_logistica", ["articulo_id"])


def downgrade():
    if (op.get_bind().execute(sa.text("SELECT 1 FROM rectificacion_logistica LIMIT 1")).first()
        or op.get_bind().execute(sa.text("SELECT 1 FROM custodia_externa WHERE cantidad_ajustada<>0 LIMIT 1")).first()):
        raise RuntimeError("Existen compensaciones logísticas: conserva sus asientos antes de revertir C04")
    op.drop_table("rectificacion_logistica")
    op.drop_constraint("ck_custodia_balance", "custodia_externa", type_="check")
    op.create_check_constraint("ck_custodia_balance", "custodia_externa",
                               "cantidad_entregada = cantidad_fuera + cantidad_vendida + cantidad_devuelta")
    op.drop_column("custodia_externa", "cantidad_ajustada")
