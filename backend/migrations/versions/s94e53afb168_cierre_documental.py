"""Fuente explícita y evidencia de cierre por artículo; ninguna aprobación automática."""
import sqlalchemy as sa
from alembic import op

revision = "s94e53afb168"
down_revision = "r83d42fea057"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("cobertura_articulo", sa.Column("cierre_movimiento_id", sa.Integer()))
    op.add_column("cobertura_articulo", sa.Column("cierre_huella_fuente", sa.String(64)))
    op.add_column("cobertura_articulo", sa.Column("cierre_snapshot", sa.JSON(none_as_null=True)))
    op.create_foreign_key("fk_cobertura_cierre", "cobertura_articulo", "movimientos_kardex",
                          ["cierre_movimiento_id"], ["id"], ondelete="RESTRICT")
    op.create_check_constraint(
        "ck_cobertura_fuente_completa", "cobertura_articulo",
        "(cierre_movimiento_id IS NULL AND cierre_huella_fuente IS NULL AND cierre_snapshot IS NULL) OR "
        "(cierre_movimiento_id IS NOT NULL AND cierre_huella_fuente IS NOT NULL AND cierre_snapshot IS NOT NULL)")


def downgrade():
    if op.get_bind().execute(sa.text(
        "SELECT count(*) FROM cobertura_articulo WHERE cierre_movimiento_id IS NOT NULL"
    )).scalar_one():
        raise RuntimeError("Hay cierres revisados: conserva sus decisiones antes de revertir C02")
    op.drop_constraint("ck_cobertura_fuente_completa", "cobertura_articulo", type_="check")
    op.drop_constraint("fk_cobertura_cierre", "cobertura_articulo", type_="foreignkey")
    for campo in ("cierre_snapshot", "cierre_huella_fuente", "cierre_movimiento_id"):
        op.drop_column("cobertura_articulo", campo)
