"""Normalize classification states for existing modern movements.

Revision ID: b71d2e9f4a63
Revises: a45b1c7d9e20
Create Date: 2026-09-18
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "b71d2e9f4a63"
down_revision: str | Sequence[str] | None = "a45b1c7d9e20"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE movimientos_kardex
            SET area_estado = CASE
                    WHEN nodo_grafo LIKE 'Área: %'
                        THEN 'RESUELTA_AUTOMATICAMENTE'
                    ELSE 'NO_APLICA'
                END,
                referencia_estado = CASE
                    WHEN referencia_documento IS NULL
                      OR BTRIM(referencia_documento) = ''
                        THEN 'AUSENTE'
                    ELSE 'PRESENTE'
                END,
                requiere_auditoria_nodo = FALSE,
                requiere_auditoria_referencia = FALSE
            WHERE lote_id IS NULL
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE movimientos_kardex
            SET area_estado = 'PENDIENTE_HIL',
                referencia_estado = 'AUSENTE',
                requiere_auditoria_nodo = FALSE,
                requiere_auditoria_referencia = FALSE
            WHERE lote_id IS NULL
            """
        )
    )
