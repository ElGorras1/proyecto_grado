from sqlalchemy.orm import Session
from thefuzz import fuzz

from app.models.kardex import LoteCarga, MovimientoKardex
from app.schemas.kardex import ExtraccionKardexHoja, MovimientoKardexCreate
from app.services.clasificador_nodos import clasificar_movimiento


def diferencias_titulos(nombre: str, paginas: list[ExtraccionKardexHoja]) -> list[dict]:
    return [
        {"pagina": indice, "titulo_detectado": pagina.nombre_articulo}
        for indice, pagina in enumerate(paginas, 1)
        if not pagina.nombre_articulo.strip()
        or fuzz.token_set_ratio(nombre.upper(), pagina.nombre_articulo.upper()) < 65
    ]

def validar_paginas_lote(
    paginas: list[ExtraccionKardexHoja],
) -> list[str]:
    """Detecta extracciones vacías; el usuario confirma el artículo al cargar.

    Los encabezados históricos pueden variar entre páginas y no determinan
    a qué artículo se asignan los movimientos.
    """
    problemas = []

    if not paginas:
        return ["El LLM no devolvió ninguna página."]

    for indice, pagina in enumerate(paginas, start=1):
        if not pagina.filas:
            problemas.append(f"Página {indice}: no contiene movimientos extraídos.")

    return problemas


def calcular_y_validar_saldos(
    db: Session,
    articulo_id: int,
    paginas: list[ExtraccionKardexHoja],
    lote_id: int,
    imagenes_paths: list[str],
) -> list[MovimientoKardexCreate]:
    """
    Toma las páginas extraídas, valida los cálculos aritméticos usando
    el saldo histórico previo (si existe), y emite los modelos para insertar.
    """
    movimientos = []

    ultimo_movimiento = (
        db.query(MovimientoKardex)
        .filter(
            MovimientoKardex.articulo_id == articulo_id,
            MovimientoKardex.lote_id.is_not(None),
        )
        .order_by(
            MovimientoKardex.lote_id.desc(),
            MovimientoKardex.numero_pagina.desc().nullslast(),
            MovimientoKardex.orden_fila.desc().nullslast(),
            MovimientoKardex.id.desc(),
        )
        .first()
    )

    if ultimo_movimiento:
        saldo_acumulado = ultimo_movimiento.saldo_registrado
        ultima_fecha = ultimo_movimiento.fecha_movimiento
    else:
        saldo_acumulado = None
        ultima_fecha = None

    for idx_pagina, pagina in enumerate(paginas):
        ruta_imagen = imagenes_paths[idx_pagina] if idx_pagina < len(imagenes_paths) else None

        for fila in pagina.filas:
            ingreso = fila.ingresos if fila.ingresos is not None else 0
            salida = fila.salidas if fila.salidas is not None else 0

            if saldo_acumulado is None:
                if ingreso > 0 or salida > 0:
                    saldo_esperado = ingreso - salida
                else:
                    saldo_esperado = fila.saldo_registrado
            else:
                saldo_esperado = saldo_acumulado + ingreso - salida

            tiene_error = False
            obs = None

            # Validación aritmética
            if saldo_esperado != fila.saldo_registrado:
                tiene_error = True
                obs = "Error de consistencia aritmética en saldo físico."

            # Validación cronológica
            error_fecha = bool(ultima_fecha and fila.fecha < ultima_fecha)
            if error_fecha:
                obs_crono = "Error cronológico: La fecha es anterior al registro previo."
                obs = f"{obs} | {obs_crono}" if obs else obs_crono

            # Clasificación del Nodo Virtual para Teoría de Grafos
            clasificacion = clasificar_movimiento(
                detalle=fila.detalle,
                ref=fila.referencia,
                area=fila.area,
                ingreso=fila.ingresos,
                salida=fila.salidas,
                db=db,
            )

            mov = MovimientoKardexCreate(
                articulo_id=articulo_id,
                lote_id=lote_id,
                fecha_movimiento=fila.fecha,
                detalle=fila.detalle,
                referencia=fila.referencia,
                area=fila.area,
                ingresos=fila.ingresos,
                salidas=fila.salidas,
                saldo_registrado=fila.saldo_registrado,
                ruta_imagen_respaldo=ruta_imagen,
                numero_pagina=idx_pagina + 1,
                orden_fila=fila.orden_fila,
                tiene_error_saldo=tiene_error,
                fecha_original=fila.fecha,
                datos_originales={"fuente": "EXTRACCION_MLLM", **fila.model_dump(mode="json")},
                tiene_error_fecha=error_fecha,
                fecha_estado="PENDIENTE_HIL" if error_fecha else "SIN_ALERTA",
                saldo_calculado=saldo_esperado,
                observaciones=obs,
                nodo_grafo=clasificacion.nodo_grafo,
                requiere_auditoria_nodo=clasificacion.requiere_auditoria_nodo,
                area_estado=clasificacion.area_estado,
                referencia_estado=clasificacion.referencia_estado,
                requiere_auditoria_referencia=(clasificacion.requiere_auditoria_referencia),
            )
            movimientos.append(mov)

            saldo_acumulado = fila.saldo_registrado
            ultima_fecha = fila.fecha

    return movimientos


def procesar_y_guardar_lote(
    db: Session,
    articulo_id: int,
    paginas: list[ExtraccionKardexHoja],
    imagenes_paths: list[str],
    confirmar: bool = True,
) -> LoteCarga:
    try:
        # El lote y sus movimientos se confirman en una sola transacción.
        lote = LoteCarga(total_imagenes=len(imagenes_paths))
        db.add(lote)
        db.flush()

        movimientos_create = calcular_y_validar_saldos(
            db=db,
            articulo_id=articulo_id,
            paginas=paginas,
            lote_id=lote.id,
            imagenes_paths=imagenes_paths,
        )

        for movimiento in movimientos_create:
            db.add(MovimientoKardex(**movimiento.model_dump()))

        if confirmar:
            db.commit()
            db.refresh(lote)
        else:
            db.flush()
        return lote
    except Exception:
        db.rollback()
        raise


def recalcular_saldos_posteriores(db: Session, articulo_id: int, confirmar: bool = True):
    """
    Valida filas Legacy en orden físico. No altera saldos ni notas originales;
    las alertas de fecha son independientes y las confirmaciones se conservan.
    """
    movimientos = (
        db.query(MovimientoKardex)
        .filter(MovimientoKardex.articulo_id == articulo_id,
                MovimientoKardex.lote_id.isnot(None), MovimientoKardex.estado == "ACTIVO")
        .order_by(
            MovimientoKardex.lote_id.asc().nullslast(),
            MovimientoKardex.numero_pagina.asc().nullslast(),
            MovimientoKardex.orden_fila.asc().nullslast(),
            MovimientoKardex.id.asc(),
        )
        .all()
    )

    saldo_acumulado = None
    ultima_fecha = None

    for fila in movimientos:
        ingreso = fila.ingresos if fila.ingresos is not None else 0
        salida = fila.salidas if fila.salidas is not None else 0

        if saldo_acumulado is None:
            if ingreso > 0 or salida > 0:
                saldo_esperado = ingreso - salida
            else:
                saldo_esperado = fila.saldo_registrado
        else:
            saldo_esperado = saldo_acumulado + ingreso - salida

        fila.tiene_error_saldo = saldo_esperado != fila.saldo_registrado
        fila.saldo_calculado = saldo_esperado
        fila.tiene_error_fecha = bool(ultima_fecha and fila.fecha_movimiento < ultima_fecha)
        if fila.fecha_estado != "CONFIRMADA_DOCUMENTO":
            if fila.tiene_error_fecha:
                fila.fecha_estado = "PENDIENTE_HIL"
            elif fila.fecha_estado == "PENDIENTE_HIL":
                fila.fecha_estado = "SIN_ALERTA"

        saldo_acumulado = fila.saldo_registrado
        ultima_fecha = fila.fecha_movimiento

    if confirmar:
        db.commit()
    else:
        db.flush()
