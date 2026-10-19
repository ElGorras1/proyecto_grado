"""Auditoría histórica independiente del ledger."""

import sqlalchemy as sa

from alembic import op

revision = "f15a2c6e3b79"
down_revision = "e04f1b5d2a68"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "analitica_modelos",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("estado", sa.String(24), nullable=False),
        sa.Column("plaza", sa.Integer(), unique=True),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuario.id")),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("terminado_en", sa.DateTime(timezone=True)),
        sa.Column("configuracion", sa.JSON(), nullable=False),
        sa.Column("corte", sa.JSON(), nullable=False),
        sa.Column("huella", sa.String(64), nullable=False),
        sa.Column("metricas", sa.JSON()),
        sa.Column("umbral", sa.Float()),
        sa.Column("artefacto_sha256", sa.String(64)),
        sa.Column("error", sa.Text()),
    )
    op.create_table(
        "analitica_resultados",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "modelo_id", sa.String(36), sa.ForeignKey("analitica_modelos.id"), nullable=False
        ),
        sa.Column(
            "movimiento_id", sa.Integer(), sa.ForeignKey("movimientos_kardex.id"), nullable=False
        ),
        sa.Column("gestion", sa.Integer(), nullable=False),
        sa.Column("articulo_id", sa.Integer(), sa.ForeignKey("activo.id"), nullable=False),
        sa.Column("nodo", sa.String(100)),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("alerta", sa.Boolean(), nullable=False),
        sa.Column("particion", sa.String(20), nullable=False),
        sa.Column("muestra_control", sa.Boolean(), nullable=False),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.Column("contexto", sa.JSON(), nullable=False),
        sa.Column("estado_revision", sa.String(30), nullable=False),
        sa.Column("revision_numero", sa.Integer(), nullable=False),
        sa.Column("etiqueta", sa.String(30)),
        sa.UniqueConstraint("modelo_id", "movimiento_id", name="uq_analitica_modelo_movimiento"),
    )
    for col in ("modelo_id", "movimiento_id", "gestion", "articulo_id", "alerta"):
        op.create_index("ix_analitica_resultados_" + col, "analitica_resultados", [col])
    op.create_table(
        "analitica_revisiones",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "resultado_id", sa.Integer(), sa.ForeignKey("analitica_resultados.id"), nullable=False
        ),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuario.id"), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("anterior", sa.String(30), nullable=False),
        sa.Column("estado", sa.String(30), nullable=False),
        sa.Column("motivo", sa.Text(), nullable=False),
        sa.Column("etiqueta", sa.String(30)),
    )
    op.create_index(
        "ix_analitica_revisiones_resultado_id", "analitica_revisiones", ["resultado_id"]
    )


def downgrade():
    op.drop_table("analitica_revisiones")
    op.drop_table("analitica_resultados")
    op.drop_table("analitica_modelos")
