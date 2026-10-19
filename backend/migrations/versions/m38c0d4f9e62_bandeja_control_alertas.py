"""Bandeja y revisiones de avisos operativos, sin modificar el ledger."""
from alembic import op
import sqlalchemy as sa

revision = "m38c0d4f9e62"
down_revision = "l27b9c3e8d51"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("caso_control",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("articulo_id", sa.Integer(), sa.ForeignKey("activo.id"), nullable=False),
        sa.Column("movimiento_id", sa.Integer(), sa.ForeignKey("movimientos_kardex.id")),
        sa.Column("transferencia_id", sa.Integer(), sa.ForeignKey("transferencia_area.id")),
        sa.Column("custodia_id", sa.Integer(), sa.ForeignKey("custodia_externa.id")),
        sa.Column("evento_custodia_id", sa.Integer(), sa.ForeignKey("evento_custodia_externa.id")),
        sa.Column("estado", sa.String(24), nullable=False),
        sa.Column("prioridad", sa.String(10), nullable=False),
        sa.Column("asignado_id", sa.Integer(), sa.ForeignKey("usuario.id")),
        sa.Column("asignado_nombre", sa.String(120)),
        sa.Column("revision_numero", sa.Integer(), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actualizado_en", sa.DateTime(timezone=True)),
        sa.Column("conclusion", sa.String(30)),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.Column("codigos", sa.JSON(), nullable=False),
        sa.CheckConstraint("estado IN ('PENDIENTE','EN_REVISION','SEGUIMIENTO','JUSTIFICADO','CERRADO')", name="ck_caso_control_estado"),
        sa.CheckConstraint("prioridad IN ('ALTA','MEDIA','BAJA')", name="ck_caso_control_prioridad"),
        sa.CheckConstraint("(CASE WHEN movimiento_id IS NULL THEN 0 ELSE 1 END + CASE WHEN transferencia_id IS NULL THEN 0 ELSE 1 END + CASE WHEN custodia_id IS NULL THEN 0 ELSE 1 END + CASE WHEN evento_custodia_id IS NULL THEN 0 ELSE 1 END) = 1", name="ck_caso_control_origen"),
        sa.UniqueConstraint("movimiento_id", name="uq_caso_control_movimiento"),
        sa.UniqueConstraint("transferencia_id", name="uq_caso_control_transferencia"),
        sa.UniqueConstraint("custodia_id", name="uq_caso_control_custodia"),
        sa.UniqueConstraint("evento_custodia_id", name="uq_caso_control_evento"),
    )
    op.create_index("ix_caso_control_articulo_id", "caso_control", ["articulo_id"])
    op.create_index("ix_caso_control_estado", "caso_control", ["estado"])
    op.create_table("revision_control",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("caso_id", sa.Integer(), sa.ForeignKey("caso_control.id"), nullable=False),
        sa.Column("solicitud_id", sa.String(36), nullable=False),
        sa.Column("solicitud_huella", sa.String(64), nullable=False),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuario.id"), nullable=False),
        sa.Column("usuario_nombre", sa.String(120), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("anterior", sa.JSON(), nullable=False),
        sa.Column("nuevo", sa.JSON(), nullable=False),
        sa.Column("motivo", sa.Text(), nullable=False),
        sa.Column("documento", sa.String(200)),
        sa.Column("correccion_movimiento_id", sa.Integer(), sa.ForeignKey("movimientos_kardex.id")),
        sa.Column("huella_contexto", sa.String(64), nullable=False),
        sa.UniqueConstraint("solicitud_id", name="uq_revision_control_solicitud"),
    )
    op.create_index("ix_revision_control_caso_id", "revision_control", ["caso_id"])

def downgrade():
    op.drop_table("revision_control")
    op.drop_table("caso_control")
