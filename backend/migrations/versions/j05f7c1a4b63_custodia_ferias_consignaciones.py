"""Conserva como patrimonio las entregas a ferias y consignatarios."""
from alembic import op
import sqlalchemy as sa

revision = "j05f7c1a4b63"
down_revision = "i94e6b0f3a52"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("apertura_inventario", sa.Column(
        "cantidad_custodia_externa", sa.Integer(), nullable=False, server_default="0"))
    op.create_check_constraint("ck_apertura_custodia_externa", "apertura_inventario",
        "cantidad_custodia_externa >= 0 AND cantidad_custodia_externa <= 2147483647")
    op.create_table(
        "custodia_externa",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("solicitud_id", sa.String(36), nullable=False),
        sa.Column("solicitud_huella", sa.String(64), nullable=False),
        sa.Column("articulo_id", sa.Integer(), sa.ForeignKey("activo.id"), nullable=False),
        sa.Column("tipo", sa.String(20), nullable=False),
        sa.Column("area_origen_id", sa.Integer(), sa.ForeignKey("area.id"), nullable=False),
        sa.Column("receptor_nombre", sa.String(200), nullable=False),
        sa.Column("receptor_tipo", sa.String(24), nullable=False),
        sa.Column("ubicacion_externa", sa.String(200), nullable=False),
        sa.Column("ciudad", sa.String(100)),
        sa.Column("cantidad_entregada", sa.Integer(), nullable=False),
        sa.Column("cantidad_fuera", sa.Integer(), nullable=False),
        sa.Column("cantidad_vendida", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cantidad_devuelta", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_institucional_entrega", sa.Integer(), nullable=False),
        sa.Column("encargado_id", sa.Integer(), sa.ForeignKey("usuario.id"), nullable=False),
        sa.Column("registrado_por", sa.Integer(), sa.ForeignKey("usuario.id"), nullable=False),
        sa.Column("ocurrido_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("registrado_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("referencia_documento", sa.String(200), nullable=False),
        sa.Column("observaciones", sa.Text(), nullable=False),
        sa.Column("alertas_control", sa.JSON()),
        sa.Column("justificacion_alertas", sa.Text()),
        sa.UniqueConstraint("solicitud_id", name="uq_custodia_solicitud"),
        sa.CheckConstraint("tipo IN ('FERIA', 'CONSIGNACION')", name="ck_custodia_tipo"),
        sa.CheckConstraint("receptor_tipo IN ('PERSONA', 'INSTITUCION')", name="ck_custodia_receptor_tipo"),
        sa.CheckConstraint("cantidad_entregada > 0 AND cantidad_fuera >= 0 AND cantidad_vendida >= 0 AND cantidad_devuelta >= 0", name="ck_custodia_cantidades"),
        sa.CheckConstraint("cantidad_entregada = cantidad_fuera + cantidad_vendida + cantidad_devuelta", name="ck_custodia_balance"),
    )
    op.create_index("ix_custodia_articulo", "custodia_externa", ["articulo_id"])
    op.create_table(
        "evento_custodia_externa",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("solicitud_id", sa.String(36), nullable=False),
        sa.Column("solicitud_huella", sa.String(64), nullable=False),
        sa.Column("custodia_id", sa.Integer(), sa.ForeignKey("custodia_externa.id"), nullable=False),
        sa.Column("articulo_id", sa.Integer(), sa.ForeignKey("activo.id"), nullable=False),
        sa.Column("tipo", sa.String(12), nullable=False),
        sa.Column("cantidad", sa.Integer(), nullable=False),
        sa.Column("area_destino_id", sa.Integer(), sa.ForeignKey("area.id")),
        sa.Column("comprador", sa.String(200)),
        sa.Column("encargado_id", sa.Integer(), sa.ForeignKey("usuario.id"), nullable=False),
        sa.Column("registrado_por", sa.Integer(), sa.ForeignKey("usuario.id"), nullable=False),
        sa.Column("ocurrido_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("registrado_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("referencia_documento", sa.String(200), nullable=False),
        sa.Column("observaciones", sa.Text(), nullable=False),
        sa.Column("alertas_control", sa.JSON()),
        sa.Column("justificacion_alertas", sa.Text()),
        sa.Column("total_institucional_despues", sa.Integer(), nullable=False),
        sa.Column("cantidad_fuera_despues", sa.Integer(), nullable=False),
        sa.UniqueConstraint("solicitud_id", name="uq_evento_custodia_solicitud"),
        sa.CheckConstraint("tipo IN ('VENTA', 'RETORNO')", name="ck_evento_custodia_tipo"),
        sa.CheckConstraint("cantidad > 0", name="ck_evento_custodia_cantidad"),
    )
    op.create_index("ix_evento_custodia_entrega", "evento_custodia_externa", ["custodia_id"])
    op.create_index("ix_evento_custodia_articulo", "evento_custodia_externa", ["articulo_id"])


def downgrade():
    op.drop_index("ix_evento_custodia_articulo", table_name="evento_custodia_externa")
    op.drop_index("ix_evento_custodia_entrega", table_name="evento_custodia_externa")
    op.drop_table("evento_custodia_externa")
    op.drop_index("ix_custodia_articulo", table_name="custodia_externa")
    op.drop_table("custodia_externa")
    op.drop_constraint("ck_apertura_custodia_externa", "apertura_inventario", type_="check")
    op.drop_column("apertura_inventario", "cantidad_custodia_externa")
