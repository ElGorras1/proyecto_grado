"""Stock moderno basado en un cierre documental congelado al empezar a operar."""
from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo
from fastapi import HTTPException
from sqlalchemy import func
from app.models.auditoria import AuditoriaSistema
from app.models.activos import Activo, Existencia
from app.models.area import Area
from app.models.inventario import AperturaInventario, CustodiaExterna
from app.models.kardex import MovimientoKardex, SolicitudCargaKardex


def ultimos_cierres_kardex(db):
    """Última fila física por artículo: lote, página y orden de fila."""
    m = MovimientoKardex
    ranking = db.query(
        m.id.label("movimiento_id"),
        func.row_number().over(
            partition_by=m.articulo_id,
            order_by=(m.lote_id.desc(), func.coalesce(m.orden_pagina_validado, m.numero_pagina).desc(),
                      m.orden_fila.desc(), m.id.desc()),
        ).label("orden"),
    ).filter(m.lote_id.isnot(None), m.estado == "ACTIVO").subquery()
    return {cierre.articulo_id: cierre for cierre in db.query(m).join(
        ranking, m.id == ranking.c.movimiento_id,
    ).filter(ranking.c.orden == 1).all()}


def ultimo_cierre_kardex(db, articulo_id):
    m = MovimientoKardex
    return db.query(m).filter(
        m.articulo_id == articulo_id, m.lote_id.isnot(None), m.estado == "ACTIVO",
    ).order_by(m.lote_id.desc(), func.coalesce(m.orden_pagina_validado, m.numero_pagina).desc(),
               m.orden_fila.desc(), m.id.desc()).first()


def base_kardex_dict(cierre):
    if cierre is None:
        return None
    revision = cierre.revision_documental or {}
    motivo = None
    if cierre.saldo_registrado < 0 or cierre.saldo_registrado > 2147483647:
        motivo = "El saldo final del Kárdex está fuera del rango válido."
    elif cierre.tiene_error_saldo:
        motivo = "El saldo final tiene una alerta matemática pendiente de revisión."
    gestion_actual = datetime.now(ZoneInfo("America/La_Paz")).year
    if motivo is None and cierre.fecha_movimiento >= date(gestion_actual, 1, 1):
        motivo = f"La última fila histórica tiene fecha de {gestion_actual} o posterior."
    return {
        "saldo": cierre.saldo_registrado,
        "saldo_documental": revision.get("saldo_documental", cierre.saldo_registrado),
        "origen_saldo": revision.get("origen_saldo", "EXTRACCION_DIGITAL"),
        "origen_fecha": revision.get("origen_fecha", "EXTRACCION_DIGITAL"),
        "hallazgos_documentales": revision.get("hallazgos", []),
        "movimiento_id": cierre.id,
        "lote_id": cierre.lote_id,
        "fecha_movimiento": cierre.fecha_movimiento,
        "operable": motivo is None,
        "motivo_bloqueo": motivo,
    }


def asegurar_apertura_desde_kardex(db, articulo_id, usuario, request,
                                  *, devolver_estado=False):
    """Fija el saldo histórico dentro de la primera transacción moderna."""
    from app.services.cierre_anual import verificar_periodo_abierto
    verificar_periodo_abierto(db)
    articulo = db.query(Activo).filter_by(id=articulo_id).with_for_update().first()
    if articulo is None:
        raise HTTPException(404, "Artículo no encontrado")
    existente = db.query(AperturaInventario).filter_by(
        articulo_id=articulo_id).populate_existing().with_for_update().first()
    if existente is not None:
        return (existente, False) if devolver_estado else existente
    en_curso = db.query(SolicitudCargaKardex.id).filter(
        SolicitudCargaKardex.articulo_id == articulo_id,
        SolicitudCargaKardex.estado.in_(("PROCESANDO", "PENDIENTE")),
    ).first()
    if en_curso:
        raise HTTPException(409, "Este artículo tiene un escaneo en proceso o pendiente de confirmar.")
    cierre = ultimo_cierre_kardex(db, articulo_id)
    if cierre is None:
        raise HTTPException(409, "Este artículo no tiene saldo histórico. Registra un conteo físico de apertura.")
    base = base_kardex_dict(cierre)
    if not base["operable"]:
        raise HTTPException(409, base["motivo_bloqueo"])
    ultimo_moderno = db.query(func.max(MovimientoKardex.id)).filter(
        MovimientoKardex.articulo_id == articulo_id,
        MovimientoKardex.lote_id.is_(None),
    ).scalar() or 0
    apertura = AperturaInventario(
        articulo_id=articulo_id, cantidad_inicial=cierre.saldo_registrado,
        cantidad_actual=cierre.saldo_registrado, ultimo_moderno_id=ultimo_moderno,
        cantidad_sin_ubicacion=cierre.saldo_registrado,
        aprobado_por=usuario.id, aprobado_en=datetime.now(UTC),
        referencia_documento=f"Kárdex digital · lote {cierre.lote_id}, movimiento {cierre.id}",
        justificacion="Saldo final del Kárdex histórico tomado como base documental del inventario moderno; no representa un conteo físico.",
        origen="KARDEX_HISTORICO", movimiento_historico_id=cierre.id,
        lote_historico_id=cierre.lote_id,
    )
    db.add(apertura)
    db.flush()
    auditar(db, usuario, request, "activar_base_kardex_inventario", "apertura_inventario",
            articulo_id, {"saldo": cierre.saldo_registrado, "movimiento_historico_id": cierre.id,
                          "lote_historico_id": cierre.lote_id,
                          "ultimo_moderno_id": ultimo_moderno})
    return (apertura, True) if devolver_estado else apertura


def bloquear_apertura(db, articulo_id):
    from app.services.cierre_anual import verificar_periodo_abierto
    verificar_periodo_abierto(db)
    apertura = db.query(AperturaInventario).filter_by(articulo_id=articulo_id).populate_existing().with_for_update().first()
    if apertura is None:
        raise HTTPException(409, "Un administrador debe aprobar el saldo de apertura tras verificar el conteo físico.")
    return apertura


def cambiar_existencia_area(db, apertura, area_id: int | None, delta: int,
                            *, exigir_area_activa: bool = True):
    """Ajusta una ubicación dentro del bloqueo del artículo/apertura."""
    if area_id is None:
        nuevo = apertura.cantidad_sin_ubicacion + delta
        if nuevo < 0:
            raise HTTPException(409, "La cantidad sin ubicación confirmada es insuficiente. Indica el área que entrega.")
        apertura.cantidad_sin_ubicacion = nuevo
        return
    area = db.get(Area, area_id)
    if area is None or (exigir_area_activa and area.estado != "activo"):
        raise HTTPException(422, "Selecciona un área operativa activa.")
    row = db.query(Existencia).filter_by(activo_id=apertura.articulo_id,
                                         area_id=area_id).with_for_update().first()
    if row is None:
        if delta < 0:
            raise HTTPException(409, f"El área {area.nombre} no tiene unidades asignadas.")
        row = Existencia(activo_id=apertura.articulo_id, area_id=area_id,
                         cantidad=0, estado="activo")
        db.add(row)
    nuevo = int(row.cantidad) + delta
    if nuevo < 0:
        raise HTTPException(409, f"Stock insuficiente en el área {area.nombre}.")
    row.cantidad = nuevo


def cantidad_efectiva_movimiento(db, movimiento):
    """Cantidad vigente después de rectificaciones; no reescribe el asiento original."""
    ultima = db.query(MovimientoKardex.cantidad_corregida).filter(
        MovimientoKardex.corrige_movimiento_id == movimiento.id,
        MovimientoKardex.estado == "ACTIVO",
    ).order_by(MovimientoKardex.id.desc()).first()
    return int(ultima[0] if ultima else (movimiento.ingresos or movimiento.salidas or 0))


def cantidad_devuelta_efectiva(db, venta_id, *, excluir_id=None):
    retornos = db.query(MovimientoKardex).filter(
        MovimientoKardex.movimiento_origen_id == venta_id,
        MovimientoKardex.estado == "ACTIVO",
    ).all()
    return sum(cantidad_efectiva_movimiento(db, retorno) for retorno in retornos
               if retorno.id != excluir_id)


def verificar_distribucion(db, apertura):
    db.flush()
    asignado = db.query(func.coalesce(func.sum(Existencia.cantidad), 0)).filter(
        Existencia.activo_id == apertura.articulo_id).scalar()
    fuera = db.query(func.coalesce(func.sum(CustodiaExterna.cantidad_fuera), 0)).filter(
        CustodiaExterna.articulo_id == apertura.articulo_id).scalar()
    if int(fuera) != apertura.cantidad_custodia_externa:
        raise RuntimeError("La custodia externa no coincide con sus entregas abiertas")
    if int(asignado) + apertura.cantidad_sin_ubicacion + int(fuera) != apertura.cantidad_actual:
        raise RuntimeError("La distribución por áreas y custodia no coincide con el stock institucional")


def distribucion_dict(db, articulo_id, apertura=None, base=None):
    if apertura is None:
        saldo = base["saldo"] if base else None
        return {"articulo_id": articulo_id, "total_institucional": saldo,
                "sin_ubicacion_confirmada": saldo,
                "en_custodia_externa": 0,
                "areas": [], "estado": "BASE_DOCUMENTAL_SIN_DISTRIBUIR" if base else "SIN_APERTURA"}
    rows = db.query(Existencia, Area.nombre).join(Area, Area.id == Existencia.area_id).filter(
        Existencia.activo_id == articulo_id).order_by(Area.nombre).all()
    return {"articulo_id": articulo_id,
            "total_institucional": apertura.cantidad_actual,
            "sin_ubicacion_confirmada": apertura.cantidad_sin_ubicacion,
            "en_custodia_externa": apertura.cantidad_custodia_externa,
            "areas": [{"area_id": e.area_id, "area": nombre, "cantidad": int(e.cantidad)}
                      for e, nombre in rows],
            "estado": "DISTRIBUCION_PARCIAL" if apertura.cantidad_sin_ubicacion else "DISTRIBUCION_COMPLETA"}


def auditar(db, usuario, request, accion, recurso, recurso_id, detalle):
    # Sin commit propio: stock, movimiento y evidencia se confirman juntos.
    db.add(AuditoriaSistema(usuario_id=usuario.id, accion=accion,
        recurso=recurso, recurso_id=recurso_id, resultado="exito",
        fecha_hora=datetime.now(UTC), ip_origen=request.client.host if request.client else None,
        detalle=detalle))


def apertura_dict(a):
    if a is None:
        return None
    return {k: getattr(a, k) for k in (
        "articulo_id", "cantidad_inicial", "cantidad_actual", "cantidad_sin_ubicacion",
        "cantidad_custodia_externa", "ultimo_moderno_id",
        "aprobado_por", "aprobado_en", "referencia_documento", "justificacion",
        "origen", "movimiento_historico_id", "lote_historico_id")}
