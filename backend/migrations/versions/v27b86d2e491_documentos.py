"""Adjuntos privados por articulo y referencia documental."""
from alembic import op
import sqlalchemy as sa
revision = 'v27b86d2e491'
down_revision = 'u16a75c1d380'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('documento_operativo',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('articulo_id', sa.Integer(), sa.ForeignKey('activo.id'), nullable=False),
        sa.Column('referencia', sa.String(200), nullable=False),
        sa.Column('nombre', sa.String(180), nullable=False),
        sa.Column('archivo', sa.String(40), nullable=False, unique=True),
        sa.Column('tipo', sa.String(50), nullable=False),
        sa.Column('bytes', sa.Integer(), nullable=False),
        sa.Column('sha256', sa.String(64), nullable=False),
        sa.Column('registrado_por', sa.Integer(), sa.ForeignKey('usuario.id'), nullable=False),
        sa.Column('registrado_en', sa.DateTime(timezone=True), nullable=False))
    op.create_index('ix_documento_operativo_articulo_id', 'documento_operativo', ['articulo_id'])


def downgrade():
    if op.get_bind().execute(sa.text('SELECT 1 FROM documento_operativo LIMIT 1')).first():
        raise RuntimeError('Conserva los documentos antes de revertir su esquema')
    op.drop_table('documento_operativo')
