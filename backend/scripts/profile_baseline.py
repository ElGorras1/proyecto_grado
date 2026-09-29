"""Genera una línea base reproducible de la base y las evidencias del Kárdex.

El script abre una transacción PostgreSQL de solo lectura, no imprime la cadena
de conexión y no modifica datos. Su salida JSON puede conservarse junto al
backup previo a una migración para reconciliar conteos, stock y archivos.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, text

from app.core.config import settings

TABLES = (
    "movimientos_kardex",
    "lotes_carga",
    "activo",
    "usuario",
    "auditoria_sistema",
    "catalogo_areas",
    "catalogo_ferias",
    "sinonimos_area",
    "existencia",
    "movimiento",
    "documento_legacy",
    "extraccion_legacy",
    "validacion_legacy",
    "resultado_regla",
    "evaluacion_anomalia",
    "alerta",
    "caso_auditoria",
    "revision_caso",
)


def json_default(value: Any) -> str | int | float:
    if isinstance(value, date | datetime):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    raise TypeError(f"Tipo no serializable: {type(value).__name__}")


def scalar(conn, statement: str) -> Any:
    return conn.execute(text(statement)).scalar_one()


def database_profile() -> dict[str, Any]:
    engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

    try:
        with engine.connect() as conn:
            transaction = conn.begin()
            try:
                conn.execute(text("SET TRANSACTION READ ONLY"))

                available_tables = set(
                    conn.execute(
                        text("SELECT tablename FROM pg_tables " "WHERE schemaname = 'public'")
                    ).scalars()
                )
                table_counts = {
                    table: scalar(conn, f'SELECT COUNT(*) FROM "{table}"')
                    for table in TABLES
                    if table in available_tables
                }

                movement_summary = dict(
                    conn.execute(
                        text(
                            """
                            SELECT
                                COUNT(*) AS total,
                                COUNT(*) FILTER (WHERE lote_id IS NOT NULL) AS legacy,
                                COUNT(*) FILTER (WHERE lote_id IS NULL) AS moderno,
                                COUNT(*) FILTER (WHERE estado = 'ANULADO') AS anulados,
                                COUNT(DISTINCT articulo_id) AS articulos,
                                COUNT(DISTINCT lote_id) FILTER (
                                    WHERE lote_id IS NOT NULL
                                ) AS lotes,
                                MIN(fecha_movimiento) AS fecha_minima,
                                MAX(fecha_movimiento) AS fecha_maxima,
                                COUNT(*) FILTER (
                                    WHERE tiene_error_saldo IS TRUE
                                ) AS errores_rojos,
                                COUNT(*) FILTER (
                                    WHERE requiere_auditoria_nodo IS TRUE
                                ) AS errores_amarillos,
                                COUNT(*) FILTER (
                                    WHERE tiene_error_saldo IS TRUE
                                      AND requiere_auditoria_nodo IS TRUE
                                ) AS errores_rojos_y_amarillos,
                                COUNT(*) FILTER (
                                    WHERE nodo_grafo IS NULL
                                       OR BTRIM(nodo_grafo) = ''
                                ) AS sin_nodo
                            FROM movimientos_kardex
                            """
                        )
                    )
                    .mappings()
                    .one()
                )

                duplicate_rows = int(
                    scalar(
                        conn,
                        """
                        SELECT COALESCE(SUM(repeticiones - 1), 0)
                        FROM (
                            SELECT COUNT(*) AS repeticiones
                            FROM movimientos_kardex
                            GROUP BY
                                articulo_id,
                                fecha_movimiento,
                                COALESCE(detalle, ''),
                                COALESCE(referencia, ''),
                                COALESCE(area, ''),
                                COALESCE(ingresos, 0),
                                COALESCE(salidas, 0),
                                saldo_registrado
                            HAVING COUNT(*) > 1
                        ) AS posibles_duplicados
                        """,
                    )
                )

                stock_rows = (
                    conn.execute(
                        text(
                            """
                        SELECT
                            a.id AS articulo_id,
                            a.codigo,
                            COALESCE(ultimo.saldo_registrado, 0) AS saldo,
                            ultimo.movimiento_id
                        FROM activo AS a
                        LEFT JOIN LATERAL (
                            SELECT
                                mk.id AS movimiento_id,
                                mk.saldo_registrado
                            FROM movimientos_kardex AS mk
                            WHERE mk.articulo_id = a.id
                            ORDER BY mk.id DESC
                            LIMIT 1
                        ) AS ultimo ON TRUE
                        ORDER BY a.id
                        """
                        )
                    )
                    .mappings()
                    .all()
                )
                stock_payload = [dict(row) for row in stock_rows]
                stock_canonical = json.dumps(
                    stock_payload,
                    default=json_default,
                    ensure_ascii=False,
                    separators=(",", ":"),
                    sort_keys=True,
                ).encode("utf-8")
                stock_summary = {
                    "articulos": len(stock_payload),
                    "saldo_total_segun_ultimo_movimiento": sum(
                        int(row["saldo"] or 0) for row in stock_payload
                    ),
                    "sha256": hashlib.sha256(stock_canonical).hexdigest(),
                }

                audit_summary = [
                    dict(row)
                    for row in conn.execute(
                        text(
                            """
                            SELECT accion, resultado, COUNT(*) AS total
                            FROM auditoria_sistema
                            GROUP BY accion, resultado
                            ORDER BY accion, resultado
                            """
                        )
                    ).mappings()
                ]
            finally:
                transaction.rollback()
    finally:
        engine.dispose()

    return {
        "tablas": table_counts,
        "movimientos_kardex": movement_summary,
        "posibles_duplicados_exactos": duplicate_rows,
        "stock_actual": stock_summary,
        "auditoria_por_accion_resultado": audit_summary,
    }


def evidence_profile(storage_dir: Path) -> dict[str, Any]:
    files = sorted(path for path in storage_dir.rglob("*") if path.is_file())
    manifest_lines: list[str] = []
    total_bytes = 0

    for path in files:
        relative_path = path.relative_to(storage_dir).as_posix()
        size = path.stat().st_size
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        total_bytes += size
        manifest_lines.append(f"{relative_path}|{size}|{digest}")

    manifest = "\n".join(manifest_lines).encode("utf-8")
    return {
        "directorio": storage_dir.as_posix(),
        "archivos": len(files),
        "bytes": total_bytes,
        "sha256_manifiesto": hashlib.sha256(manifest).hexdigest(),
    }


def main() -> None:
    backend_dir = Path(__file__).resolve().parents[1]
    storage_dir = backend_dir / "storage" / "kardex_images"
    result = {
        "generado_en_utc": datetime.now(UTC).isoformat(),
        "modo": "solo_lectura",
        "base_de_datos": database_profile(),
        "evidencias": evidence_profile(storage_dir),
    }
    print(json.dumps(result, default=json_default, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
