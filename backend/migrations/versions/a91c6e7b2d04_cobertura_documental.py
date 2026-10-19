"""Cobertura documental declarada sin inferir completitud del OCR."""
from alembic import op
import sqlalchemy as sa

revision = "a91c6e7b2d04"
down_revision = "f83c9a1e2d47"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "cobertura_articulo",
        sa.Column("articulo_id", sa.Integer(), sa.ForeignKey("activo.id"), primary_key=True),
        sa.Column("estado", sa.String(24), nullable=False),
        sa.Column("referencia", sa.String(255), nullable=False),
        sa.Column("observacion", sa.Text(), nullable=False),
        sa.Column("ultimo_lote_revisado_id", sa.Integer()),
        sa.Column("revisado_por", sa.Integer(), sa.ForeignKey("usuario.id"), nullable=False),
        sa.Column("revisado_en", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("estado IN ('SIN_CONFIRMAR', 'PARCIAL', 'CIERRE_CONFIRMADO')",
                           name="ck_cobertura_articulo_estado"),
    )
    op.create_table(
        "tramo_cobertura",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("articulo_id", sa.Integer(), sa.ForeignKey("activo.id"), nullable=False),
        sa.Column("gestion_desde", sa.Integer(), nullable=False),
        sa.Column("gestion_hasta", sa.Integer(), nullable=False),
        sa.Column("estado", sa.String(20), nullable=False),
        sa.Column("paginas_faltantes", sa.Integer()),
        sa.Column("descripcion", sa.Text(), nullable=False),
        sa.Column("referencia", sa.String(255), nullable=False),
        sa.Column("revisado_por", sa.Integer(), sa.ForeignKey("usuario.id"), nullable=False),
        sa.Column("revisado_en", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("gestion_desde <= gestion_hasta", name="ck_tramo_periodo"),
        sa.CheckConstraint("estado IN ('PENDIENTE', 'SIN_CONFIRMAR', 'CONFIRMADO')",
                           name="ck_tramo_estado"),
        sa.CheckConstraint("paginas_faltantes IS NULL OR paginas_faltantes >= 0",
                           name="ck_tramo_paginas_faltantes"),
    )
    op.create_index("ix_tramo_cobertura_articulo_id", "tramo_cobertura", ["articulo_id"])


def downgrade():
    op.drop_index("ix_tramo_cobertura_articulo_id", table_name="tramo_cobertura")
    op.drop_table("tramo_cobertura")
    op.drop_table("cobertura_articulo")
