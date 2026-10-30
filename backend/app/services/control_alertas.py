"""Crea un caso por operación alertada dentro de la transacción original."""
import hashlib
import json
from datetime import UTC, datetime
from sqlalchemy import func
from app.models.control_alertas import CasoControl
from app.models.kardex import MovimientoKardex
from app.models.inventario import TransferenciaArea, CustodiaExterna, EventoCustodiaExterna

ORIGENES = {
    "MOVIMIENTO": (MovimientoKardex, "movimiento_id"),
    "TRANSFERENCIA": (TransferenciaArea, "transferencia_id"),
    "CUSTODIA": (CustodiaExterna, "custodia_id"),
    "EVENTO_CUSTODIA": (EventoCustodiaExterna, "evento_custodia_id"),
}

def huella(datos):
    return hashlib.sha256(json.dumps(datos, sort_keys=True, ensure_ascii=False, default=str,
        separators=(",", ":")).encode()).hexdigest()

def fecha(valor):
    if valor is None:
        return None
    return (valor if valor.tzinfo else valor.replace(tzinfo=UTC)).isoformat()

def operacion(fila, clase):
    comun = dict(clase=clase, id=fila.id, articulo_id=fila.articulo_id,
        ocurrido_en=fecha(fila.ocurrido_en), registrado_en=fecha(fila.registrado_en),
        documento=fila.referencia_documento, encargado_id=fila.encargado_id,
        justificacion_operador=fila.justificacion_alertas, alertas=fila.alertas_control or [])
    if clase == "MOVIMIENTO":
        comun.update(tipo=fila.tipo_operacion, cantidad=(fila.ingresos or 0) + (fila.salidas or 0),
            direccion="INGRESO" if fila.ingresos else "SALIDA", area_origen_id=fila.area_operativa_id,
            area_destino_id=None, receptor=fila.receptor or fila.devuelto_por,
            registrador_id=fila.usuario_registrador_id, saldo_registrado=fila.saldo_registrado,
            corrige_movimiento_id=fila.corrige_movimiento_id)
    elif clase == "TRANSFERENCIA":
        comun.update(tipo="Transferencia entre áreas", cantidad=fila.cantidad, direccion="TRASLADO",
            area_origen_id=fila.area_origen_id, area_destino_id=fila.area_destino_id,
            receptor=None, registrador_id=fila.registrado_por, saldo_registrado=fila.total_institucional)
    elif clase == "CUSTODIA":
        comun.update(tipo=fila.tipo, cantidad=fila.cantidad_entregada, direccion="ENTREGA_EXTERNA",
            area_origen_id=fila.area_origen_id, area_destino_id=None, receptor=fila.receptor_nombre,
            registrador_id=fila.registrado_por, saldo_registrado=fila.total_institucional_entrega,
            ubicacion_externa=fila.ubicacion_externa, ciudad=fila.ciudad)
    else:
        comun.update(tipo=fila.tipo, cantidad=fila.cantidad, direccion=fila.tipo,
            area_origen_id=None, area_destino_id=fila.area_destino_id, receptor=fila.comprador,
            registrador_id=fila.registrado_por, saldo_registrado=fila.total_institucional_despues,
            custodia_id=fila.custodia_id)
    return comun

def registrar_caso(db, fila, clase):
    from app.services.analitica_operativa import puntuar_nueva

    puntuar_nueva(db, fila, clase)
    if not fila.alertas_control or (clase == "MOVIMIENTO" and fila.lote_id is not None):
        return None
    if fila.id is None:
        db.flush()
    columna = ORIGENES[clase][1]
    existente = db.query(CasoControl).filter(getattr(CasoControl, columna) == fila.id).first()
    if existente:
        return existente
    caso = CasoControl(articulo_id=fila.articulo_id, **{columna: fila.id},
        creado_en=fila.registrado_en or datetime.now(UTC), estado="PENDIENTE",
        prioridad="ALTA" if any(a["nivel"] == "alto" for a in fila.alertas_control) else "MEDIA",
        revision_numero=0, snapshot=operacion(fila, clase),
        codigos=sorted({a["codigo"] for a in fila.alertas_control}))
    db.add(caso)
    db.flush()
    return caso

def incorporar_avisos_guardados(db):
    cantidad = 0
    for clase, (modelo, columna) in ORIGENES.items():
        q = db.query(modelo).filter(modelo.alertas_control.isnot(None))
        if clase == "MOVIMIENTO":
            q = q.filter(modelo.lote_id.is_(None))
        for fila in q:
            if fila.alertas_control and not db.query(CasoControl.id).filter(getattr(CasoControl, columna) == fila.id).first():
                registrar_caso(db, fila, clase)
                cantidad += 1
    db.flush()
    return cantidad

def contexto_actual(db, caso):
    from app.services.rectificaciones_logisticas import estado_vigente
    for clase, (modelo, columna) in ORIGENES.items():
        origen = getattr(caso, columna)
        if origen is not None:
            fila = db.get(modelo, origen)
            datos = operacion(fila, clase)
            if clase in ("TRANSFERENCIA", "CUSTODIA", "EVENTO_CUSTODIA"):
                vigente, _, rect = estado_vigente(db, "ENTREGA" if clase == "CUSTODIA" else clase, fila)
                datos.update(datos_vigentes=vigente, ultima_rectificacion_logistica_id=rect.id if rect else None)
            if clase == "MOVIMIENTO":
                from app.services.inventario import cantidad_efectiva_movimiento
                datos.update(cantidad_vigente=cantidad_efectiva_movimiento(db, fila),
                    ultima_rectificacion_id=db.query(func.max(MovimientoKardex.id)).filter(
                        MovimientoKardex.corrige_movimiento_id == fila.id).scalar())
            if clase == "CUSTODIA":
                datos.update(cantidad_fuera=fila.cantidad_fuera, cantidad_vendida=fila.cantidad_vendida,
                             cantidad_devuelta=fila.cantidad_devuelta)
            if clase == "EVENTO_CUSTODIA":
                c = db.get(CustodiaExterna, fila.custodia_id)
                datos.update(cantidad_fuera=c.cantidad_fuera, cantidad_vendida=c.cantidad_vendida,
                             cantidad_devuelta=c.cantidad_devuelta, receptor_custodia=c.receptor_nombre,
                             ubicacion_externa=c.ubicacion_externa, ciudad=c.ciudad)
            return datos
    raise ValueError("Caso sin origen")
