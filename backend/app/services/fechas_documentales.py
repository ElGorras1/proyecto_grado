"""Distingue la fecha escrita de una fecha técnica conservada para consulta."""

from sqlalchemy import and_, or_

ESTADOS_INCOMPLETOS = ("SIN_FECHA_DOCUMENTAL", "FECHA_PARCIAL", "FECHA_ILEGIBLE")
ESTADO_PRECISION = {
    "AUSENTE": "SIN_FECHA_DOCUMENTAL",
    "PARCIAL": "FECHA_PARCIAL",
    "ILEGIBLE": "FECHA_ILEGIBLE",
}
ORIGENES_TECNICOS = ("HIPOTESIS", "SECUENCIA_AJUSTADA")


def fecha_asignable(m):
    """Permite agrupar por año solo fechas completas sin procedencia hipotética."""
    rev = m.revision_documental or {}
    return bool(
        m.fecha_movimiento
        and m.fecha_estado not in (*ESTADOS_INCOMPLETOS, "ESTIMADA_HIL")
        and rev.get("origen_fecha") not in ORIGENES_TECNICOS
    )


def fecha_asignable_sql():
    from app.models.kardex import MovimientoKardex as M

    origen = M.revision_documental["origen_fecha"].as_string()
    return and_(
        M.fecha_movimiento.isnot(None),
        M.fecha_estado.notin_((*ESTADOS_INCOMPLETOS, "ESTIMADA_HIL")),
        or_(origen.is_(None), origen.notin_(ORIGENES_TECNICOS)),
    )


def fecha_pendiente_sql():
    from app.models.kardex import MovimientoKardex as M

    return or_(
        M.fecha_estado.in_(("PENDIENTE_HIL", *ESTADOS_INCOMPLETOS)), M.fecha_movimiento.is_(None)
    )


def datos_fecha(m):
    rev = m.revision_documental or {}
    return {
        "fecha_documental_texto": m.fecha_documental_texto
        if m.fecha_documental_texto is not None
        else rev.get("fecha_documental"),
        "fecha_precision": m.fecha_precision
        or rev.get("fecha_precision")
        or ("COMPLETA" if m.fecha_movimiento else "AUSENTE"),
        "gestion_confirmada": m.fecha_movimiento.year if fecha_asignable(m) else None,
    }
