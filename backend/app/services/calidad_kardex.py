"""Una definición de pendientes para HIL, reportes y dashboard."""
from sqlalchemy import or_
from app.models.kardex import MovimientoKardex as M
from app.services.clasificador_nodos import ESTADOS_AREA_PENDIENTES
from app.services.fechas_documentales import ESTADOS_INCOMPLETOS, fecha_pendiente_sql


def pendiente_hil_sql():
    return or_(M.tiene_error_saldo.is_(True), fecha_pendiente_sql(),
               M.requiere_auditoria_nodo.is_(True), M.requiere_auditoria_referencia.is_(True),
               M.area_estado.in_(ESTADOS_AREA_PENDIENTES),
               M.referencia_estado.in_(("ILEGIBLE", "INCIERTA")))


def tipos_alerta(m):
    tipos = []
    if m.tiene_error_saldo:
        tipos.append("saldo")
    if m.fecha_movimiento is None or m.fecha_estado in ("PENDIENTE_HIL", *ESTADOS_INCOMPLETOS):
        tipos.append("fecha")
    if m.requiere_auditoria_nodo or m.area_estado in ESTADOS_AREA_PENDIENTES:
        tipos.append("area")
    if m.requiere_auditoria_referencia or m.referencia_estado in ("ILEGIBLE", "INCIERTA"):
        tipos.append("referencia")
    return tipos


def snapshot_original(m, fuente="BASELINE_PREVIA_CORRECCION"):
    return {"fuente": fuente, "fecha_movimiento": m.fecha_movimiento.isoformat() if m.fecha_movimiento else None,
            "detalle": m.detalle, "area": m.area, "referencia": m.referencia,
            "ingresos": m.ingresos, "salidas": m.salidas, "saldo_registrado": m.saldo_registrado}
