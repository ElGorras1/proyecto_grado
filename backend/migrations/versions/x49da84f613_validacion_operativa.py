"""Muestras de cotejo para el modelo digital."""

import sqlalchemy as sa
from alembic import op

revision = "x49da84f613"
down_revision = "w38c97e3f502"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "estudio_operativo",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("modelo_id", sa.String(36), sa.ForeignKey("analitica_operativa_modelos.id"), nullable=False),
        sa.Column("creador_id", sa.Integer(), sa.ForeignKey("usuario.id"), nullable=False),
        sa.Column("gestion", sa.Integer(), nullable=False),
        sa.Column("simulado", sa.Boolean(), nullable=False),
        sa.Column("poblacion", sa.Integer(), nullable=False),
        sa.Column("semilla", sa.Integer(), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "cotejo_operativo",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("estudio_id", sa.Integer(), sa.ForeignKey("estudio_operativo.id"), nullable=False),
        sa.Column("resultado_id", sa.Integer(), sa.ForeignKey("analitica_operativa_resultados.id"), nullable=False),
        sa.Column("evidencia", sa.JSON(), nullable=False),
        sa.Column("prediccion", sa.Boolean(), nullable=False),
        sa.Column("etiqueta", sa.String(20)),
        sa.Column("motivo", sa.Text()),
        sa.Column("respaldo", sa.String(250)),
        sa.Column("revisor_id", sa.Integer(), sa.ForeignKey("usuario.id")),
        sa.Column("revisado_en", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("estudio_id", "resultado_id", name="uq_cotejo_operativo_resultado"),
        sa.CheckConstraint("etiqueta IN ('ANOMALO', 'NORMAL', 'INDETERMINADO')", name="ck_cotejo_operativo_etiqueta"),
    )
    op.create_index("ix_cotejo_operativo_estudio_id", "cotejo_operativo", ["estudio_id"])


def downgrade():
    if op.get_bind().execute(sa.text("SELECT 1 FROM estudio_operativo LIMIT 1")).first():
        raise RuntimeError("Conserva los estudios de cotejo antes de revertir el esquema.")
    op.drop_table("cotejo_operativo")
    op.drop_table("estudio_operativo")
