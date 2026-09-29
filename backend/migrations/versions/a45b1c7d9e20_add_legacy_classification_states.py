"""Add explicit area and reference classification states.

Revision ID: a45b1c7d9e20
Revises: c23f251d5769
Create Date: 2026-09-18
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a45b1c7d9e20"
down_revision: str | Sequence[str] | None = "c23f251d5769"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "movimientos_kardex",
        sa.Column(
            "area_estado",
            sa.String(length=40),
            nullable=False,
            server_default="PENDIENTE_HIL",
        ),
    )
    op.add_column(
        "movimientos_kardex",
        sa.Column(
            "referencia_estado",
            sa.String(length=20),
            nullable=False,
            server_default="AUSENTE",
        ),
    )
    op.add_column(
        "movimientos_kardex",
        sa.Column(
            "requiere_auditoria_referencia",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )

    op.execute(
        sa.text(
            """
            UPDATE movimientos_kardex
            SET area_estado = CASE
                    WHEN area IS NULL OR BTRIM(area) = ''
                        THEN 'SIN_AREA_REGISTRADA'
                    ELSE 'PENDIENTE_HIL'
                END,
                referencia_estado = CASE
                    WHEN referencia IS NULL
                      OR BTRIM(referencia) = ''
                      OR UPPER(BTRIM(referencia)) IN ('-', '--', 'N/A', 'S/R', 'SIN REF')
                        THEN 'AUSENTE'
                    ELSE 'PRESENTE'
                END
            """
        )
    )

    op.create_index(
        "ix_movimientos_kardex_area_estado",
        "movimientos_kardex",
        ["area_estado"],
    )
    op.create_index(
        "ix_movimientos_kardex_referencia_estado",
        "movimientos_kardex",
        ["referencia_estado"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_movimientos_kardex_referencia_estado",
        table_name="movimientos_kardex",
    )
    op.drop_index(
        "ix_movimientos_kardex_area_estado",
        table_name="movimientos_kardex",
    )
    op.drop_column("movimientos_kardex", "requiere_auditoria_referencia")
    op.drop_column("movimientos_kardex", "referencia_estado")
    op.drop_column("movimientos_kardex", "area_estado")
