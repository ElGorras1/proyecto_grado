"""Revisión documental auditable: fuente, dato vigente e inferencia separados."""
from copy import deepcopy
from datetime import UTC, date, datetime
from sqlalchemy import func
from app.models.auditoria import AuditoriaSistema
from app.models.kardex import MovimientoKardex
from app.services.calidad_kardex import snapshot_original
from app.services.fechas_documentales import ESTADOS_INCOMPLETOS, fecha_asignable

CAMPOS_EDITABLES = {"ingresos", "salidas", "saldo_registrado", "fecha_movimiento", "area", "detalle",
                    "referencia", "referencia_estado", "requiere_auditoria_referencia",
                    "orden_pagina_validado", "orden_fila", "estado", "nodo_grafo", "area_estado", "requiere_auditoria_nodo"}
ORIGENES_INFERIDOS = {"HIPOTESIS", "SECUENCIA_AJUSTADA"}

def pagina_sql():
    return func.coalesce(MovimientoKardex.orden_pagina_validado, MovimientoKardex.numero_pagina)

def snapshot_revision(m):
    return {c.name: (getattr(m, c.name).isoformat() if isinstance(getattr(m, c.name), (date, datetime))
                     else deepcopy(getattr(m, c.name))) for c in m.__table__.columns}

def aplicar_cambio(m, cambios, revision, *, criterio_sha256, plan_sha256):
    if m.lote_id is None:
        raise ValueError("La revisión documental no modifica operaciones digitales")
    if set(cambios) - CAMPOS_EDITABLES:
        raise ValueError("Campo no permitido en una revisión documental")
    if 'detalle' in cambios and (not isinstance(cambios['detalle'],str) or not cambios['detalle'].strip()):
        raise ValueError("El detalle corregido debe conservar texto documental")
    if not revision.get("motivo", "").strip() or not revision.get("criterios"):
        raise ValueError("Cada revisión requiere motivo y criterio")
    if revision.get("origen_fecha") in ORIGENES_INFERIDOS:
        if "fecha_documental" not in revision or not revision.get("motivo_fecha"):
            raise ValueError("La fecha inferida requiere la lectura documental y un motivo")
    for campo in ("ingresos", "salidas"):
        v = cambios.get(campo)
        if v is not None and (type(v) is not int or v < 0):
            raise ValueError("Una cantidad debe ser un entero no negativo")
    if "saldo_registrado" in cambios and type(cambios["saldo_registrado"]) is not int:
        raise ValueError("El saldo debe ser entero")
    if cambios.get("orden_pagina_validado") is not None and cambios["orden_pagina_validado"] < 1:
        raise ValueError("Orden de página inválido")
    if 'orden_fila' in cambios and (type(cambios['orden_fila']) is not int or cambios['orden_fila']<1):
        raise ValueError('Orden de fila inválido')
    if cambios.get("estado", m.estado) not in {"ACTIVO", "ANULADO_DOCUMENTO", "NOTA_DOCUMENTAL"}:
        raise ValueError("Estado documental no permitido")
    if m.datos_originales is None:
        m.datos_originales = snapshot_original(m)
    if m.fecha_original is None and m.datos_originales.get('fuente') != 'LECTURA_FOTO_HIL':
        m.fecha_original = m.fecha_movimiento
    anterior = deepcopy(m.revision_documental or {})
    for k, v in cambios.items():
        if k == "fecha_movimiento" and isinstance(v, str):
            v = date.fromisoformat(v)
        setattr(m, k, v)
    nuevo = {**anterior, **deepcopy(revision), "version": 1,
             "criterio_sha256": criterio_sha256, "plan_sha256": plan_sha256,
             "autor_registro": "Codex, por instrucción del usuario de este chat",
             "revisado_en": datetime.now(UTC).isoformat()}
    nuevo["criterios"] = sorted(set(anterior.get("criterios", []) + revision["criterios"]))
    nuevo["planes_aplicados"] = sorted(set(anterior.get("planes_aplicados", []) +
        ([anterior["plan_sha256"]] if anterior.get("plan_sha256") else []) + [plan_sha256]))
    nuevo["hallazgos"] = sorted(set(anterior.get("hallazgos", []) + revision.get("hallazgos", [])))
    m.revision_documental = nuevo
    if "fecha_movimiento" in cambios:
        m.fecha_estado = "ESTIMADA_HIL" if nuevo.get("origen_fecha") in ORIGENES_INFERIDOS else "CORREGIDA"
    if m.estado != "ACTIVO":
        m.tiene_error_saldo = False
        m.tiene_error_fecha = False
        m.fecha_estado = "NO_APLICA_DOCUMENTAL"

def recalcular_revision(movimientos):
    """Calcula continuidad por tramo; conserva saldo escrito y diferencias históricas."""
    saldo = None
    fecha = None
    reconstruir = False
    for m in movimientos:
        if m.estado != "ACTIVO":
            continue
        rev = deepcopy(m.revision_documental or {})
        i, s = m.ingresos or 0, m.salidas or 0
        if "saldo_base" in rev:
            saldo = rev["saldo_base"]
        if rev.get("reconstruir_cadena"):
            reconstruir = True
        esperado = saldo + i - s if saldo is not None else (i - s if i or s else m.saldo_registrado)
        ajuste = rev.get("ajuste_disponibilidad", 0)
        if type(ajuste) is not int:
            raise ValueError("El ajuste documental de disponibilidad debe ser entero")
        esperado += ajuste
        if rev.get("tipo_fila") in {"RECUENTO", "BASE_DOCUMENTAL"}:
            if saldo is not None:
                rev["diferencia_con_cadena_previa"] = m.saldo_registrado - esperado
            esperado = m.saldo_registrado
            reconstruir = True
        if rev.get("usar_saldo_esperado"):
            m.saldo_registrado = esperado
        m.saldo_calculado = esperado
        m.tiene_error_saldo = esperado != m.saldo_registrado
        retroceso = bool(fecha and m.fecha_movimiento and m.fecha_movimiento < fecha)
        m.tiene_error_fecha = m.fecha_movimiento is None or retroceso or bool(rev.get("fecha_documental_fuera_orden"))
        if m.fecha_estado not in {"CONFIRMADA_DOCUMENTO", "ESTIMADA_HIL", *ESTADOS_INCOMPLETOS}:
            if retroceso:
                m.fecha_estado = "PENDIENTE_HIL"
            elif m.fecha_estado == "PENDIENTE_HIL":
                m.fecha_estado = "SIN_ALERTA"
        if rev:
            documental = rev.get("saldo_documental")
            if documental is not None:
                rev["diferencia_saldo_documental"] = documental - esperado
            m.revision_documental = rev
        saldo = esperado if reconstruir else m.saldo_registrado
        if fecha_asignable(m):
            fecha = m.fecha_movimiento

def registrar_revision(db, m, anterior, *, criterio_sha256, motivo, usuario_id=None):
    nuevo = snapshot_revision(m)
    if anterior == nuevo:
        return False
    db.add(AuditoriaSistema(usuario_id=usuario_id, accion="corregir_kardex_hil",
                            recurso="movimientos_kardex", recurso_id=m.id, resultado="exito",
                            fecha_hora=datetime.now(UTC),
                            detalle={"previo": anterior, "nuevo": nuevo, "motivo": motivo,
                                     "criterio_sha256": criterio_sha256,
                                     "autor_registro": "Codex, por instrucción del usuario de este chat"}))
    return True

