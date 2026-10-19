"""Controles inmediatos explicables para movimientos del inventario moderno."""
import hashlib
import hmac
import json
from datetime import UTC, datetime
from statistics import median

from app.core.config import settings

POLITICA_VERSION = "2026-10-08.2"


def parametros_control():
    return dict(hora_inicio=settings.CONTROL_HORA_INICIO, hora_fin=settings.CONTROL_HORA_FIN,
                cantidad_extrema=settings.CONTROL_CANTIDAD_EXTREMA,
                porcentaje_mayoritario=settings.CONTROL_PORCENTAJE_MAYORITARIO,
                stock_minimo_mayoritario=settings.CONTROL_STOCK_MINIMO_MAYORITARIO,
                factor_atipico=settings.CONTROL_FACTOR_ATIPICO,
                min_comparables=settings.CONTROL_MIN_COMPARABLES,
                min_cantidad_atipica=settings.CONTROL_MIN_CANTIDAD_ATIPICA,
                registro_tardio_horas=settings.CONTROL_REGISTRO_TARDIO_HORAS)


def politica_control():
    return {"version": POLITICA_VERSION, "estado": "PROVISIONAL", "zona": "America/La_Paz",
            **parametros_control(), "repeticion_minutos": settings.CONTROL_REPETICION_MINUTOS,
            "comparacion": "Hasta 20 operaciones digitales del mismo artículo, operación y ubicación, posteriores al corte; cantidades vigentes después de rectificaciones. El histórico OCR no se usa como patrón de operaciones actuales.",
            "confirmacion": "Los avisos requieren revisar, justificar y confirmar. Los límites de stock y las operaciones imposibles se bloquean."}


def evaluar_ubicacion(*, cantidad, saldo, codigo_total, codigo_mayoria, etiqueta,
                      porcentaje=80, minimo=10):
    if saldo <= 0:
        return []
    if cantidad == saldo:
        return [{"codigo": codigo_total, "nivel": "alto",
                 "mensaje": f"La operación utiliza todas las unidades de {etiqueta}.",
                 "datos": {"saldo_ubicacion": saldo, "cantidad": cantidad, "politica_version": POLITICA_VERSION}}]
    if saldo >= minimo and cantidad * 100 >= saldo * porcentaje:
        return [{"codigo": codigo_mayoria, "nivel": "alto",
                 "mensaje": f"La operación utiliza al menos el {porcentaje} % de las unidades de {etiqueta}.",
                 "datos": {"saldo_ubicacion": saldo, "cantidad": cantidad, "porcentaje": porcentaje,
                           "minimo": minimo, "politica_version": POLITICA_VERSION}}]
    return []


def aviso_repeticion(previos: list[dict], identidad: dict):
    """Previos ya acotados por artículo y ventana real de registro, nunca por OCR."""
    def normalizar(valor):
        return " ".join(valor.split()).casefold() if isinstance(valor, str) else valor
    if not (identidad.get("documento") or "").strip():
        return []
    coincidencias = sorted(p["id"] for p in previos if all(
        normalizar(p.get(campo)) == normalizar(valor) for campo, valor in identidad.items()))
    if not coincidencias:
        return []
    return [{"codigo": "POSIBLE_DUPLICADO", "nivel": "medio",
             "mensaje": "Ya existe un registro reciente con el mismo documento, cantidad y participantes o ubicaciones. Revisa el historial antes de registrar otra entrega.",
             "datos": {"registros_previos": coincidencias, "documento": identidad["documento"],
                       "ventana_minutos": settings.CONTROL_REPETICION_MINUTOS,
                       "politica_version": POLITICA_VERSION}}]


def cantidades_comparables(db, *, articulo_id, ultimo_moderno_id, tipo, operacion, area_id):
    from app.models.kardex import MovimientoKardex
    from app.services.inventario import cantidad_efectiva_movimiento
    columna = MovimientoKardex.ingresos if tipo == "ingreso" else MovimientoKardex.salidas
    filas = db.query(MovimientoKardex).filter(
        MovimientoKardex.articulo_id == articulo_id, MovimientoKardex.lote_id.is_(None),
        MovimientoKardex.id > ultimo_moderno_id, MovimientoKardex.estado == "ACTIVO",
        MovimientoKardex.corrige_movimiento_id.is_(None),
        MovimientoKardex.tipo_operacion == operacion,
        MovimientoKardex.area_operativa_id == area_id, columna > 0,
    ).order_by(MovimientoKardex.id.desc()).limit(20).all()
    return [cantidad_efectiva_movimiento(db, m) for m in filas]


def stock_ubicacion(db, apertura, area_id):
    from app.models.activos import Existencia
    if area_id is None:
        return apertura.cantidad_sin_ubicacion
    fila = db.query(Existencia).filter_by(activo_id=apertura.articulo_id, area_id=area_id).first()
    return int(fila.cantidad) if fila else 0


OPERACIONES_INGRESO = frozenset({"Inventario / Compra", "Devolución"})
OPERACIONES_SALIDA = frozenset({
    "Ventas", "Obsequios y Donaciones", "Consignación", "Baja / Pérdida",
    "Salida a Feria",
})
OPERACIONES_RECEPTOR = frozenset({
    "Ventas", "Obsequios y Donaciones", "Consignación", "Salida a Feria",
})
CATALOGO_OPERACIONES = (
    {"valor": "Inventario / Compra", "direccion": "ingreso", "requiere_receptor": False},
    {"valor": "Ventas", "direccion": "salida", "requiere_receptor": True},
    {"valor": "Obsequios y Donaciones", "direccion": "salida", "requiere_receptor": True},
    {"valor": "Consignación", "direccion": "salida", "requiere_receptor": True,
     "habilitada": False, "motivo_pendiente": "Usa Entrega externa en Inventario Actual: la consignación conserva el patrimonio hasta venta o retorno."},
    {"valor": "Salida a Feria", "direccion": "salida", "requiere_receptor": True,
     "habilitada": False, "motivo_pendiente": "Usa Entrega externa en Inventario Actual: el envío a feria conserva el total institucional."},
    {"valor": "Préstamo a Exposición", "direccion": "transferencia", "requiere_receptor": True,
     "habilitada": False, "motivo_pendiente": "Requiere institución receptora, ubicación externa, acta y control de retorno."},
    {"valor": "Baja / Pérdida", "direccion": "salida", "requiere_receptor": False},
    {"valor": "Transferencia Interna", "direccion": "transferencia", "requiere_receptor": True,
     "habilitada": False, "motivo_pendiente": "Usa el formulario Transferir entre áreas en Inventario Actual; no corresponde a una salida del stock institucional."},
    {"valor": "Devolución", "direccion": "ingreso", "requiere_receptor": False},
)


def validar_operacion(*, tipo: str, operacion: str | None, receptor: str | None,
                      feria_id: int | None, ciudad_feria: str | None,
                      motivo_baja: str | None,
                      receptor_tipo: str | None = None,
                      referencia_documento: str | None = None) -> str | None:
    """Controla combinaciones imposibles y evidencia mínima en operaciones conocidas."""
    nombre = (operacion or "").strip()
    if nombre and nombre not in {item["valor"] for item in CATALOGO_OPERACIONES}:
        return "Selecciona una operación del catálogo vigente."
    if nombre in OPERACIONES_INGRESO and tipo != "ingreso":
        return f"{nombre} debe registrarse como ingreso."
    if nombre in OPERACIONES_SALIDA and tipo != "salida":
        return f"{nombre} debe registrarse como salida."
    if receptor_tipo and not (receptor or "").strip():
        return "Indica el nombre de quien recibe."
    if nombre in OPERACIONES_RECEPTOR and not (receptor or "").strip():
        return f"{nombre} requiere identificar al receptor."
    if nombre in OPERACIONES_RECEPTOR and receptor_tipo not in {
        "PERSONA", "INSTITUCION", "PUBLICO_GENERAL"
    }:
        return f"{nombre} requiere indicar si recibe una persona o institución."
    if receptor_tipo == "PUBLICO_GENERAL":
        if nombre != "Ventas":
            return "Público general solo corresponde a una venta."
        if not (referencia_documento or "").strip():
            return "Una venta a público general requiere documento de respaldo."
    if nombre == "Salida a Feria" and not (feria_id or (ciudad_feria or "").strip()):
        return "Salida a Feria requiere la feria o la ciudad."
    if nombre == "Baja / Pérdida" and not (motivo_baja or "").strip():
        return "Baja / Pérdida requiere indicar el motivo."
    if nombre and len((referencia_documento or "").strip()) < 3:
        return "La operación requiere una referencia de acta, factura u otro documento de respaldo."
    return None


def evaluar_movimiento(
    *, tipo: str, cantidad: int, saldo: int, fecha_local: datetime,
    cantidades_previas: list[int], hora_inicio: int = 7, hora_fin: int = 20,
    cantidad_extrema: int = 1000,
    porcentaje_mayoritario: int = 80, stock_minimo_mayoritario: int = 10,
    factor_atipico: int = 3, min_comparables: int = 5, min_cantidad_atipica: int = 10,
    fecha_operacion_local: datetime | None = None, registro_tardio_horas: int = 24,
) -> list[dict]:
    """Devuelve avisos, no juicios de fraude ni bloqueos de stock."""
    avisos = []
    if tipo == "salida" and saldo > 0:
        if cantidad == saldo:
            avisos.append({"codigo": "AGOTA_STOCK", "nivel": "alto",
                           "mensaje": "La salida dejará el artículo sin existencias.",
                           "datos": {"saldo_previo": saldo, "cantidad": cantidad}})
        elif saldo >= stock_minimo_mayoritario and cantidad * 100 >= saldo * porcentaje_mayoritario:
            avisos.append({"codigo": "SALIDA_MAYORITARIA", "nivel": "alto",
                           "mensaje": f"La salida comprende al menos el {porcentaje_mayoritario} % del stock institucional disponible.",
                           "datos": {"saldo_previo": saldo, "cantidad": cantidad, "porcentaje": porcentaje_mayoritario}})
    if cantidad >= cantidad_extrema:
        avisos.append({"codigo": "CANTIDAD_EXTREMA", "nivel": "alto",
                       "mensaje": f"La cantidad alcanza {cantidad_extrema} unidades o más; verifica que no sea un error de digitación.",
                       "datos": {"cantidad": cantidad, "umbral": cantidad_extrema}})
    comparables = [valor for valor in cantidades_previas if valor > 0]
    if len(comparables) >= min_comparables:
        referencia = median(comparables)
        if cantidad >= max(min_cantidad_atipica, referencia * factor_atipico):
            avisos.append({"codigo": "CANTIDAD_ATIPICA", "nivel": "medio",
                           "mensaje": f"La cantidad alcanza al menos {factor_atipico} veces la mediana de operaciones comparables de este artículo.",
                           "datos": {"cantidad": cantidad, "mediana": referencia,
                                     "comparables": len(comparables), "factor": factor_atipico}})
    if not hora_inicio <= fecha_local.hour < hora_fin:
        avisos.append({"codigo": "FUERA_HORARIO", "nivel": "medio",
                       "mensaje": f"Registro fuera del horario provisional {hora_inicio:02d}:00–{hora_fin:02d}:00.",
                       "datos": {"fecha_local": fecha_local.isoformat(),
                                 "zona": "America/La_Paz"}})
    if fecha_operacion_local is not None:
        fuera_registro = not hora_inicio <= fecha_local.hour < hora_fin
        fuera_operacion = not hora_inicio <= fecha_operacion_local.hour < hora_fin
        if fuera_operacion and not fuera_registro:
            avisos.append({"codigo": "OPERACION_FUERA_HORARIO", "nivel": "medio",
                           "mensaje": f"La operación ocurrió fuera de {hora_inicio:02d}:00–{hora_fin:02d}:00, aunque se registra dentro del horario.",
                           "datos": {"fecha_operacion": fecha_operacion_local.isoformat(), "zona": "America/La_Paz"}})
        if fuera_operacion and fuera_registro:
            avisos[-1]["datos"]["fecha_operacion"] = fecha_operacion_local.isoformat()
            avisos[-1]["mensaje"] = f"El registro y la operación están fuera del horario provisional {hora_inicio:02d}:00–{hora_fin:02d}:00."
        demora = fecha_local.astimezone(UTC) - fecha_operacion_local.astimezone(UTC)
        if demora.total_seconds() >= registro_tardio_horas * 3600:
            avisos.append({"codigo": "REGISTRO_TARDIO", "nivel": "medio",
                           "mensaje": f"La operación se registra al menos {registro_tardio_horas} horas después de ocurrir; verifica la fecha y el respaldo.",
                           "datos": {"fecha_operacion": fecha_operacion_local.isoformat(), "umbral_horas": registro_tardio_horas}})
    for aviso in avisos:
        aviso["datos"]["politica_version"] = POLITICA_VERSION
    return avisos


def firma_confirmacion(secret: str, *, payload: dict, usuario_id: int,
                       saldo: int, hora_local: str, alertas: list[dict],
                       ultimo_movimiento_id: int) -> str:
    # La hora exacta de una alerta fuera de horario cambia entre vista previa
    # y confirmación. La hora del reloj ya se firma mediante hora_local.
    avisos_estables = [{**aviso, "datos": {
        clave: valor for clave, valor in aviso["datos"].items()
        if clave != "fecha_local"}} for aviso in alertas]
    contenido = json.dumps({"payload": payload, "usuario_id": usuario_id,
                           "saldo": saldo, "hora_local": hora_local,
                           "alertas": avisos_estables,
                           "ultimo_movimiento_id": ultimo_movimiento_id},
                          sort_keys=True, ensure_ascii=False,
                          default=str, separators=(",", ":"))
    return hmac.new(secret.encode(), contenido.encode(), hashlib.sha256).hexdigest()


def confirmar_alertas(db, payload, *, usuario_id, articulo_id, custodia_id, saldo,
                     ultimo_id, ahora, alertas, contexto=None):
    from fastapi import HTTPException
    from zoneinfo import ZoneInfo
    if alertas:
        firma = firma_confirmacion(settings.JWT_SECRET_KEY,
            payload=payload.model_dump(exclude={"confirmacion_alertas", "motivo_alertas"})
                    | {"articulo_id": articulo_id, "custodia_id": custodia_id, **(contexto or {})},
            usuario_id=usuario_id, saldo=saldo,
            hora_local=ahora.astimezone(ZoneInfo("America/La_Paz")).strftime("%Y-%m-%dT%H"),
            alertas=alertas, ultimo_movimiento_id=ultimo_id)
        if not payload.confirmacion_alertas or not hmac.compare_digest(payload.confirmacion_alertas, firma):
            db.rollback()
            raise HTTPException(409, detail={"codigo": "ALERTAS_CONTROL", "alertas": alertas,
                "firma_confirmacion": firma, "saldo_previo": saldo})
        if len(payload.motivo_alertas.strip()) < 10:
            db.rollback()
            raise HTTPException(422, "Justifica la operación alertada con al menos 10 caracteres.")
    elif payload.confirmacion_alertas:
        db.rollback()
        raise HTTPException(409, detail={"codigo": "CONTROL_DESACTUALIZADO",
            "mensaje": "La operación cambió; vuelve a revisarla antes de guardar."})
