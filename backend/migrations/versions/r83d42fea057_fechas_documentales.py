"""Fechas históricas ausentes/parciales, conservando la primera lectura."""

import sqlalchemy as sa
from alembic import op

revision = "r83d42fea057"
down_revision = "q72c31ed9f46"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("movimientos_kardex", sa.Column("fecha_documental_texto", sa.String(100)))
    op.add_column("movimientos_kardex", sa.Column("fecha_precision", sa.String(20)))
    op.alter_column(
        "movimientos_kardex", "fecha_movimiento", existing_type=sa.Date(), nullable=True
    )
    op.create_check_constraint(
        "ck_kardex_fecha_digital",
        "movimientos_kardex",
        "lote_id IS NOT NULL OR fecha_movimiento IS NOT NULL",
    )
    op.create_check_constraint(
        "ck_kardex_precision_fecha",
        "movimientos_kardex",
        "fecha_precision IS NULL OR (fecha_precision = 'COMPLETA' AND fecha_movimiento IS NOT NULL) OR (fecha_precision IN ('PARCIAL','AUSENTE','ILEGIBLE') AND fecha_movimiento IS NULL)",
    )


def downgrade():
    # Una reversión nunca inventa fechas ni descarta nuevas lecturas documentales.
    if (
        op.get_bind()
        .execute(
            sa.text(
                "SELECT count(*) FROM movimientos_kardex WHERE fecha_movimiento IS NULL OR fecha_documental_texto IS NOT NULL OR fecha_precision IS NOT NULL"
            )
        )
        .scalar_one()
    ):
        raise RuntimeError("Hay fechas/documentos nuevos: conserva sus datos antes de revertir N01")
    op.drop_constraint("ck_kardex_precision_fecha", "movimientos_kardex", type_="check")
    op.drop_constraint("ck_kardex_fecha_digital", "movimientos_kardex", type_="check")
    op.alter_column(
        "movimientos_kardex", "fecha_movimiento", existing_type=sa.Date(), nullable=False
    )
    op.drop_column("movimientos_kardex", "fecha_precision")
    op.drop_column("movimientos_kardex", "fecha_documental_texto")
