"""Política periódica y seguimiento sin modificar cortes de evaluación."""

from alembic import op
import sqlalchemy as sa

revision = "w38c97e3f502"
down_revision = "v27b86d2e491"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "politica_analitica",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "modelo_base_id", sa.String(36), sa.ForeignKey("analitica_modelos.id"), nullable=False
        ),
        sa.Column("habilitada", sa.Boolean(), nullable=False),
        sa.Column("preparar_candidatos", sa.Boolean(), nullable=False),
        sa.Column("gestion_hasta", sa.Integer(), nullable=False),
        sa.Column("intervalo_segundos", sa.Integer(), nullable=False),
        sa.Column("revision_dias", sa.Integer(), nullable=False),
        sa.Column("ultimo_analisis", sa.DateTime(timezone=True)),
        sa.Column("ultima_revision", sa.DateTime(timezone=True)),
        sa.Column("ultimo_informe", sa.JSON()),
        sa.Column("ultimo_error", sa.Text()),
        sa.Column("candidato_id", sa.String(36), sa.ForeignKey("analitica_modelos.id")),
        sa.Column("huella_revision", sa.String(64)),
        sa.CheckConstraint("id=1", name="ck_politica_analitica_unica"),
        sa.CheckConstraint("gestion_hasta BETWEEN 1900 AND 9998", name="ck_politica_gestion"),
        sa.CheckConstraint("intervalo_segundos BETWEEN 60 AND 86400", name="ck_politica_intervalo"),
        sa.CheckConstraint("revision_dias BETWEEN 1 AND 365", name="ck_politica_revision"),
    )
    op.create_table(
        "resultado_seguimiento",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "modelo_id", sa.String(36), sa.ForeignKey("analitica_modelos.id"), nullable=False
        ),
        sa.Column(
            "movimiento_id", sa.Integer(), sa.ForeignKey("movimientos_kardex.id"), nullable=False
        ),
        sa.Column("articulo_id", sa.Integer(), sa.ForeignKey("activo.id"), nullable=False),
        sa.Column("gestion", sa.Integer(), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("huella_snapshot", sa.String(64), nullable=False),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.Column("contexto", sa.JSON(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("alerta", sa.Boolean(), nullable=False),
        sa.Column("estado_revision", sa.String(30), nullable=False),
        sa.Column("revision_numero", sa.Integer(), nullable=False),
        sa.Column("etiqueta", sa.String(30)),
        sa.UniqueConstraint(
            "modelo_id", "movimiento_id", "huella_snapshot", name="uq_seguimiento_version"
        ),
    )
    op.create_index(
        "ix_resultado_seguimiento_movimiento_id", "resultado_seguimiento", ["movimiento_id"]
    )
    op.create_index(
        "ix_resultado_seguimiento_articulo_id", "resultado_seguimiento", ["articulo_id"]
    )
    op.create_table(
        "revision_seguimiento",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "resultado_id", sa.Integer(), sa.ForeignKey("resultado_seguimiento.id"), nullable=False
        ),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuario.id"), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("anterior", sa.String(30), nullable=False),
        sa.Column("estado", sa.String(30), nullable=False),
        sa.Column("etiqueta", sa.String(30), nullable=False),
        sa.Column("motivo", sa.Text(), nullable=False),
    )


def downgrade():
    for tabla in ("revision_seguimiento", "resultado_seguimiento", "politica_analitica"):
        if op.get_bind().execute(sa.text(f"SELECT 1 FROM {tabla} LIMIT 1")).first():
            raise RuntimeError(
                "Conserva la política y el seguimiento antes de revertir su esquema."
            )
    op.drop_table("revision_seguimiento")
    op.drop_table("resultado_seguimiento")
    op.drop_table("politica_analitica")
