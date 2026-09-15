from typing import List, Tuple
from sqlalchemy.orm import Session
from app.models.kardex import LoteCarga, MovimientoKardex
from app.schemas.kardex import ExtraccionKardexHoja, MovimientoKardexCreate
from datetime import datetime
from app.services.clasificador_nodos import clasificar_nodo_movimiento

def calcular_y_validar_saldos(
    db: Session,
    articulo_id: int,
    paginas: List[ExtraccionKardexHoja],
    lote_id: int,
    imagenes_paths: List[str]
) -> List[MovimientoKardexCreate]:
    """
    Toma las páginas extraídas, valida los cálculos aritméticos usando 
    el saldo histórico previo (si existe), y emite los modelos para insertar.
    """
    movimientos = []
    
    ultimo_movimiento = db.query(MovimientoKardex)\
        .filter(MovimientoKardex.articulo_id == articulo_id)\
        .order_by(MovimientoKardex.fecha_movimiento.desc(), MovimientoKardex.numero_pagina.desc(), MovimientoKardex.orden_fila.desc())\
        .first()
        
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
            if ultima_fecha and fila.fecha < ultima_fecha:
                tiene_error = True
                obs_crono = "Error cronológico: La fecha es anterior al registro previo."
                obs = f"{obs} | {obs_crono}" if obs else obs_crono
            
            # Clasificación del Nodo Virtual para Teoría de Grafos
            nodo_grafo, requiere_auditoria_nodo = clasificar_nodo_movimiento(
                detalle=fila.detalle,
                ref=fila.referencia,
                area=fila.area,
                ingreso=fila.ingresos,
                salida=fila.salidas
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
                saldo_calculado=saldo_esperado,
                observaciones=obs,
                nodo_grafo=nodo_grafo,
                requiere_auditoria_nodo=requiere_auditoria_nodo
            )
            movimientos.append(mov)
            
            saldo_acumulado = fila.saldo_registrado
            ultima_fecha = fila.fecha
            
    return movimientos

def procesar_y_guardar_lote(
    db: Session, 
    articulo_id: int, 
    paginas: List[ExtraccionKardexHoja], 
    imagenes_paths: List[str]
) -> LoteCarga:
    
    # 1. Crear el lote
    lote = LoteCarga(total_imagenes=len(imagenes_paths))
    db.add(lote)
    db.commit()
    db.refresh(lote)
    
    # 2. Validar y preparar los modelos
    movimientos_create = calcular_y_validar_saldos(
        db=db,
        articulo_id=articulo_id,
        paginas=paginas,
        lote_id=lote.id,
        imagenes_paths=imagenes_paths
    )
    
    # 3. Insertar en bloque
    for mc in movimientos_create:
        db_mov = MovimientoKardex(**mc.model_dump())
        db.add(db_mov)
        
    db.commit()
    return lote

def recalcular_saldos_posteriores(db: Session, articulo_id: int):
    """
    Recalcula la consistencia matemática de TODAS las filas de un artículo (orden cronológico)
    y limpia la bandera de error si la corrección hizo cuadrar la fila.
    """
    movimientos = db.query(MovimientoKardex)\
        .filter(MovimientoKardex.articulo_id == articulo_id)\
        .order_by(MovimientoKardex.fecha_movimiento.asc(), MovimientoKardex.numero_pagina.asc(), MovimientoKardex.orden_fila.asc())\
        .all()
        
    saldo_acumulado = None
    
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
            
        if saldo_esperado != fila.saldo_registrado:
            fila.tiene_error_saldo = True
            fila.saldo_calculado = saldo_esperado
            fila.observaciones = "Error de consistencia aritmética en saldo físico."
        else:
            fila.tiene_error_saldo = False
            fila.saldo_calculado = saldo_esperado
            fila.observaciones = None
            
        saldo_acumulado = fila.saldo_registrado
        
    db.commit()

