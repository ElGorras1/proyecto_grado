"""Baja lógica de alias y unicidad de nombres/códigos sin distinguir mayúsculas."""
import sqlalchemy as sa
from alembic import op

revision = "t05f64b0c279"
down_revision = "s94e53afb168"
branch_labels = None
depends_on = None
INDICES = (
    ("uq_area_nombre_normalizado", "area", "nombre"),
    ("uq_area_codigo_normalizado", "area", "codigo"),
    ("uq_catalogo_nombre_normalizado", "catalogo_areas", "nombre_oficial"),
    ("uq_catalogo_abrev_normalizada", "catalogo_areas", "abreviatura"),
    ("uq_alias_texto_normalizado", "sinonimos_area", "texto_sucio"),
)


def upgrade():
    for _, tabla, campo in INDICES:
        if op.get_bind().execute(sa.text(
            f"SELECT 1 FROM {tabla} WHERE {campo} IS NOT NULL GROUP BY upper(trim({campo})) HAVING count(*)>1 LIMIT 1"
        )).first():
            raise RuntimeError("Hay claves duplicadas: revisa el catálogo antes de migrar C03")
    op.add_column("sinonimos_area", sa.Column("activa", sa.Boolean(), nullable=False, server_default=sa.true()))
    for nombre, tabla, campo in INDICES:
        op.create_index(nombre, tabla, [sa.text(f"upper(trim({campo}))")], unique=True)


def downgrade():
    if op.get_bind().execute(sa.text("SELECT 1 FROM sinonimos_area WHERE activa=FALSE LIMIT 1")).first():
        raise RuntimeError("Hay alias desactivados: conserva sus decisiones antes de revertir C03")
    for nombre, tabla, _ in reversed(INDICES):
        op.drop_index(nombre, table_name=tabla)
    op.drop_column("sinonimos_area", "activa")
