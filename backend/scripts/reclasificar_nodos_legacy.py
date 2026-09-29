"""Reclasifica nodos legacy conservando siempre el texto OCR original.

Por defecto solo muestra el impacto. Use ``--apply`` para confirmar cambios.
"""

import argparse
import json
from collections import Counter

from app.db.session import SessionLocal
from app.models.kardex import MovimientoKardex
from app.services.clasificador_nodos import (
    ESTADOS_AREA_PENDIENTES,
    ESTADOS_REFERENCIA_PENDIENTES,
    clasificar_movimiento,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Persiste la reclasificación. Sin esta opción se revierte todo.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    db = SessionLocal()
    resumen = Counter()
    estados_area = Counter()
    estados_referencia = Counter()

    try:
        movimientos = (
            db.query(
                MovimientoKardex.id,
                MovimientoKardex.detalle,
                MovimientoKardex.referencia,
                MovimientoKardex.area,
                MovimientoKardex.ingresos,
                MovimientoKardex.salidas,
                MovimientoKardex.nodo_grafo,
                MovimientoKardex.requiere_auditoria_nodo,
            )
            .filter(MovimientoKardex.lote_id.isnot(None))
            .order_by(MovimientoKardex.id)
            .all()
        )

        for movimiento in movimientos:
            clasificacion = clasificar_movimiento(
                detalle=movimiento.detalle,
                ref=movimiento.referencia,
                area=movimiento.area,
                ingreso=movimiento.ingresos,
                salida=movimiento.salidas,
                db=db,
            )
            resumen["evaluados"] += 1
            resumen["pendientes_hil_area"] += int(
                clasificacion.area_estado in ESTADOS_AREA_PENDIENTES
            )
            resumen["pendientes_hil_referencia"] += int(
                clasificacion.referencia_estado in ESTADOS_REFERENCIA_PENDIENTES
            )
            resumen["filas_con_hil"] += int(
                clasificacion.requiere_auditoria_nodo or clasificacion.requiere_auditoria_referencia
            )
            estados_area[clasificacion.area_estado] += 1
            estados_referencia[clasificacion.referencia_estado] += 1

            if (
                movimiento.nodo_grafo != clasificacion.nodo_grafo
                or movimiento.requiere_auditoria_nodo != clasificacion.requiere_auditoria_nodo
            ):
                resumen["cambios_nodo"] += 1

            if args.apply:
                db.query(MovimientoKardex).filter(MovimientoKardex.id == movimiento.id).update(
                    {
                        MovimientoKardex.nodo_grafo: clasificacion.nodo_grafo,
                        MovimientoKardex.area_estado: clasificacion.area_estado,
                        MovimientoKardex.referencia_estado: (clasificacion.referencia_estado),
                        MovimientoKardex.requiere_auditoria_nodo: (
                            clasificacion.requiere_auditoria_nodo
                        ),
                        MovimientoKardex.requiere_auditoria_referencia: (
                            clasificacion.requiere_auditoria_referencia
                        ),
                    },
                    synchronize_session=False,
                )

        if args.apply:
            db.commit()
            modo = "APLICADO"
        else:
            db.rollback()
            modo = "SIMULACION"

        salida = {
            "modo": modo,
            **resumen,
            "estados_area": dict(estados_area),
            "estados_referencia": dict(estados_referencia),
        }
        print(json.dumps(salida, ensure_ascii=False, indent=2))
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
