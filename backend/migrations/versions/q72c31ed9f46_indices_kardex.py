"""Índices para consultas por artículo, cierre físico y lote; no modifica filas."""
import sqlalchemy as sa
from alembic import op

revision = "q72c31ed9f46"
down_revision = "p61b20dc8e35"
branch_labels = None
depends_on = None


def upgrade():
    if op.get_bind().dialect.name == "postgresql":
        op.execute("SET LOCAL lock_timeout = '5s'")
        op.execute("SET LOCAL statement_timeout = '60s'")
    op.create_index("ix_kardex_articulo_orden", "movimientos_kardex",
        ["articulo_id", "estado", "lote_id",
         sa.text("coalesce(orden_pagina_validado, numero_pagina)"), "orden_fila", "id"])
    op.create_index("ix_kardex_lote", "movimientos_kardex", ["lote_id"])


def downgrade():
    op.drop_index("ix_kardex_lote", table_name="movimientos_kardex")
    op.drop_index("ix_kardex_articulo_orden", table_name="movimientos_kardex")
