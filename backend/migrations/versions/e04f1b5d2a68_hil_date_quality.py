"""Separate chronology from arithmetic and preserve the original baseline.

Existing data are a baseline, not a claim to recover past overwritten OCR.
"""
from alembic import op
import sqlalchemy as sa

revision = "e04f1b5d2a68"
down_revision = "d93f0a4c1e57"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("movimientos_kardex", sa.Column("fecha_original", sa.Date()))
    op.add_column("movimientos_kardex", sa.Column("datos_originales", sa.JSON()))
    op.add_column("movimientos_kardex", sa.Column("tiene_error_fecha", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("movimientos_kardex", sa.Column("fecha_estado", sa.String(30), nullable=False, server_default="SIN_ALERTA"))
    op.execute("""
        UPDATE movimientos_kardex SET fecha_original = fecha_movimiento,
        datos_originales = json_build_object('fuente', 'BASELINE_MIGRACION',
          'fecha_movimiento', fecha_movimiento, 'detalle', detalle, 'area', area,
          'referencia', referencia, 'ingresos', ingresos, 'salidas', salidas,
          'saldo_registrado', saldo_registrado)
    """)
    op.execute("""
        WITH secuencia AS (
          SELECT id, saldo_registrado, fecha_movimiento, ingresos, salidas,
            row_number() OVER orden AS posicion,
            lag(saldo_registrado) OVER orden AS saldo_previo,
            lag(fecha_movimiento) OVER orden AS fecha_previa
          FROM movimientos_kardex WHERE lote_id IS NOT NULL AND estado = 'ACTIVO'
          WINDOW orden AS (PARTITION BY articulo_id ORDER BY lote_id,
            numero_pagina NULLS LAST, orden_fila NULLS LAST, id)
        ), calculo AS (
          SELECT id, saldo_registrado,
            CASE WHEN posicion = 1 AND coalesce(ingresos,0) = 0 AND coalesce(salidas,0) = 0
              THEN saldo_registrado
              ELSE coalesce(saldo_previo,0) + coalesce(ingresos,0) - coalesce(salidas,0) END AS esperado,
            coalesce(fecha_movimiento < fecha_previa, false) AS error_fecha
          FROM secuencia
        )
        UPDATE movimientos_kardex m SET saldo_calculado = c.esperado,
          tiene_error_saldo = (c.esperado != c.saldo_registrado),
          tiene_error_fecha = c.error_fecha,
          fecha_estado = CASE WHEN c.error_fecha THEN 'PENDIENTE_HIL' ELSE 'SIN_ALERTA' END
        FROM calculo c WHERE m.id = c.id
    """)
    op.create_index("ix_kardex_fecha_estado", "movimientos_kardex", ["fecha_movimiento", "estado"])


def downgrade():
    op.drop_index("ix_kardex_fecha_estado", "movimientos_kardex")
    # La bandera antigua representaba ambos errores.
    op.execute("UPDATE movimientos_kardex SET tiene_error_saldo = tiene_error_saldo OR tiene_error_fecha")
    for nombre in ("fecha_estado", "tiene_error_fecha", "datos_originales", "fecha_original"):
        op.drop_column("movimientos_kardex", nombre)
