from collections import defaultdict
import hashlib
import json
from app.models.inventario import TransferenciaArea, CustodiaExterna, EventoCustodiaExterna
from app.models.rectificacion_logistica import RectificacionLogistica as R

MODELOS = {"TRANSFERENCIA": TransferenciaArea, "ENTREGA": CustodiaExterna, "EVENTO_CUSTODIA": EventoCustodiaExterna}
COLUMNAS = {"TRANSFERENCIA": R.transferencia_id, "ENTREGA": R.custodia_id, "EVENTO_CUSTODIA": R.evento_custodia_id}
CAMPOS = {
    "TRANSFERENCIA": ("area_origen_id", "area_destino_id"),
    "ENTREGA": ("tipo", "area_origen_id", "receptor_nombre", "receptor_tipo", "ubicacion_externa", "ciudad"),
    "EVENTO_CUSTODIA": ("tipo", "area_destino_id", "comprador"),
}


def ultima(db, clase, id):
    return db.query(R).filter(R.clase == clase, COLUMNAS[clase] == id).order_by(R.id.desc()).first()


def original(clase, fila):
    return {**{c: getattr(fila, c) for c in CAMPOS[clase]},
            "cantidad": fila.cantidad_entregada if clase == "ENTREGA" else fila.cantidad,
            "encargado_id": fila.encargado_id, "referencia_documento": fila.referencia_documento,
            "observaciones": fila.observaciones}


def estado_vigente(db, clase, fila):
    rect = ultima(db, clase, fila.id)
    nuevo = rect.nuevo if rect else original(clase, fila)
    custodia = (fila if clase == "ENTREGA" else db.get(CustodiaExterna, fila.custodia_id)
                if clase == "EVENTO_CUSTODIA" else None)
    datos = dict(clase=clase, id=fila.id, vigente=nuevo, ultima_id=rect.id if rect else None,
                 contadores=[custodia.cantidad_fuera, custodia.cantidad_vendida, custodia.cantidad_devuelta,
                             custodia.cantidad_ajustada] if custodia else None)
    version = hashlib.sha256(json.dumps(datos, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    if clase == "EVENTO_CUSTODIA":
        entrega_rectificada = ultima(db, "ENTREGA", custodia.id)
        datos["ultima_entrega_rectificada_id"] = entrega_rectificada.id if entrega_rectificada else None
        version = hashlib.sha256(json.dumps(datos, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return nuevo, version, rect


def efectos(clase, datos):
    areas = defaultdict(int)
    q = datos["cantidad"]
    total, fuera, vendida, devuelta = 0, 0, 0, 0
    if clase == "TRANSFERENCIA":
        areas[datos["area_origen_id"]] -= q
        areas[datos["area_destino_id"]] += q
    elif clase == "ENTREGA":
        areas[datos["area_origen_id"]] -= q
        fuera = q
    else:
        fuera = -q
        if datos["tipo"] == "VENTA":
            total, vendida = -q, q
        else:
            areas[datos["area_destino_id"]] += q
            devuelta = q
    return dict(areas=dict(areas), total=total, fuera=fuera, vendida=vendida, devuelta=devuelta)


def diferencia(clase, previo, nuevo):
    antes, despues = efectos(clase, previo), efectos(clase, nuevo)
    areas = {id: despues["areas"].get(id, 0) - antes["areas"].get(id, 0)
             for id in antes["areas"].keys() | despues["areas"].keys()}
    return {**{c: despues[c] - antes[c] for c in ("total", "fuera", "vendida", "devuelta")},
            "areas": {id: delta for id, delta in areas.items() if delta}}


def registro_dict(db, fila):
    from app.models.usuario import Usuario
    actor = db.get(Usuario, fila.registrado_por)
    return {c: getattr(fila, c) for c in (
        "id", "clase", "articulo_id", "transferencia_id", "custodia_id", "evento_custodia_id",
        "anterior_id", "previo", "nuevo", "areas_delta", "delta_total", "delta_custodia",
        "total_despues", "custodia_despues", "registrado_por", "registrado_en", "referencia_documento", "motivo"
    )} | {"registrador": actor.nombre if actor else None}
