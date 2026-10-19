"""Separa revisión documental, orden validado y artículos observados."""
import sqlalchemy as sa
from alembic import op

revision = "p61b20dc8e35"
down_revision = "o50a19cb7d24"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("movimientos_kardex", sa.Column("orden_pagina_validado", sa.Integer(), nullable=True))
    op.add_column("movimientos_kardex", sa.Column("revision_documental", sa.JSON(), nullable=True))
    op.add_column("activo", sa.Column("observacion_hil", sa.JSON(), nullable=True))
    op.create_check_constraint("ck_orden_pagina_validado", "movimientos_kardex", "orden_pagina_validado IS NULL OR orden_pagina_validado > 0")


def downgrade():
    bind = op.get_bind()
    if bind.execute(sa.text("SELECT count(*) FROM movimientos_kardex WHERE revision_documental IS NOT NULL OR orden_pagina_validado IS NOT NULL")).scalar_one() or bind.execute(sa.text("SELECT count(*) FROM activo WHERE observacion_hil IS NOT NULL")).scalar_one():
        raise RuntimeError("Existen revisiones documentales; conserva su evidencia antes de retirar el esquema")
    op.drop_constraint("ck_orden_pagina_validado", "movimientos_kardex", type_="check")
    op.drop_column("movimientos_kardex", "revision_documental")
    op.drop_column("movimientos_kardex", "orden_pagina_validado")
    op.drop_column("activo", "observacion_hil")
