from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy import case, distinct, func, or_
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.activos import Activo
from app.models.inventario import AperturaInventario
from app.models.kardex import MovimientoKardex as M, LoteCarga
from app.services.calidad_kardex import pendiente_hil_sql
from app.services.fechas_documentales import fecha_pendiente_sql
from app.services.clasificador_nodos import ESTADOS_AREA_PENDIENTES
from app.services.cierre_documental import fuentes_cierre

router = APIRouter(prefix="/reportes", tags=["Reportes"])


@router.get("/dashboard")
def resumen_dashboard(gestion: int = Query(..., ge=1900, le=2100),
                      db: Session = Depends(get_db), _usuario=Depends(get_current_user)):
    activo = M.estado == "ACTIVO"
    historico = M.lote_id.isnot(None)
    pendientes = pendiente_hil_sql()
    cantidad_articulos = db.query(func.count(Activo.id)).scalar()
    # La apertura ya incorpora ajustes modernos. Sin ella, usar la última
    # operación digital o el cierre físico; un ID de importación no es un cierre.
    ranking = db.query(M.id.label("id"), M.articulo_id.label("articulo_id"),
        func.row_number().over(partition_by=M.articulo_id, order_by=(
            case((M.lote_id.is_(None), 1), else_=0).desc(), M.lote_id.desc(),
            func.coalesce(M.orden_pagina_validado, M.numero_pagina).desc(),
            M.orden_fila.desc(), M.id.desc(),
        )).label("orden")).filter(activo).subquery()
    ultimos = db.query(ranking.c.id, ranking.c.articulo_id).filter(ranking.c.orden == 1).subquery()
    saldo_actual = func.coalesce(AperturaInventario.cantidad_actual, M.saldo_registrado)
    stock, con_movimiento, sin_stock = db.query(
        func.coalesce(func.sum(saldo_actual), 0), func.count(saldo_actual),
        func.coalesce(func.sum(case((saldo_actual <= 0, 1), else_=0)), 0),
    ).select_from(Activo).outerjoin(ultimos, ultimos.c.articulo_id == Activo.id).outerjoin(
        M, ultimos.c.id == M.id).outerjoin(
        AperturaInventario, AperturaInventario.articulo_id == Activo.id).one()
    # Los cierres revisados prevalecen sobre propuestas por orden de carga.
    # Se conserva el comportamiento de saldos digitales anteriores sin apertura.
    fuentes = fuentes_cierre(db)
    aperturas = {a.articulo_id for a in db.query(AperturaInventario)}
    previos = dict(db.query(ultimos.c.articulo_id, M.saldo_registrado).join(M, M.id == ultimos.c.id).all())
    for aid, fuente in fuentes.items():
        if aid in aperturas or not fuente.cierre or not fuente.revision or not fuente.revision.cierre_movimiento_id:
            continue
        anterior, seleccionado = previos.get(aid), fuente.cierre.saldo_registrado
        stock += seleccionado - (anterior or 0)
        con_movimiento += int(anterior is None)
        sin_stock += int(seleccionado <= 0) - int(anterior is not None and anterior <= 0)
    calidad = db.query(
        func.count(M.id),
        func.coalesce(func.sum(case((pendientes, 1), else_=0)), 0),
        func.coalesce(func.sum(case((M.tiene_error_saldo.is_(True), 1), else_=0)), 0),
        func.coalesce(func.sum(case((fecha_pendiente_sql(), 1), else_=0)), 0),
        func.coalesce(func.sum(case((or_(M.requiere_auditoria_nodo.is_(True), M.area_estado.in_(ESTADOS_AREA_PENDIENTES)), 1), else_=0)), 0),
        func.coalesce(func.sum(case((or_(M.requiere_auditoria_referencia.is_(True), M.referencia_estado.in_(("ILEGIBLE", "INCIERTA"))), 1), else_=0)), 0),
        func.count(distinct(M.articulo_id)),
    ).filter(activo, historico).one()
    lotes = db.query(M.lote_id.label("id")).filter(activo, historico).distinct().subquery()
    paginas, cantidad_lotes = db.query(func.coalesce(func.sum(LoteCarga.total_imagenes), 0),
                                      func.count(LoteCarga.id)).join(lotes, lotes.c.id == LoteCarga.id).one()
    operativas = db.query(M).filter(activo, M.lote_id.is_(None),
                                   M.fecha_movimiento >= date(gestion, 1, 1),
                                   M.fecha_movimiento < date(gestion + 1, 1, 1))
    operaciones, ingresos, salidas = operativas.with_entities(
        func.count(M.id), func.coalesce(func.sum(M.ingresos), 0), func.coalesce(func.sum(M.salidas), 0)
    ).one()
    meses = operativas.with_entities(func.extract("month", M.fecha_movimiento),
                                     func.coalesce(func.sum(M.ingresos), 0),
                                     func.coalesce(func.sum(M.salidas), 0)).group_by(func.extract("month", M.fecha_movimiento)).all()
    mensual = {int(m): (int(i), int(s)) for m, i, s in meses}
    prioridad = db.query(Activo.id, Activo.nombre, func.count(M.id).label("pendientes")).join(
        M, M.articulo_id == Activo.id
    ).filter(activo, historico, pendientes).group_by(Activo.id, Activo.nombre).order_by(func.count(M.id).desc(), Activo.id).limit(6).all()
    recientes = operativas.join(Activo, Activo.id == M.articulo_id).with_entities(
        M.id, Activo.nombre, M.fecha_movimiento, M.tipo_operacion, M.ingresos, M.salidas, M.usuario_operador
    ).order_by(M.id.desc()).limit(8).all()
    total, pendiente, saldo, fecha, area, referencia, digitalizados = map(int, calidad)
    return {
        "gestion": gestion,
        "inventario": {"articulos": cantidad_articulos, "saldo_ultimo_registrado": int(stock),
                       "articulos_sin_movimientos": cantidad_articulos - con_movimiento,
                       "articulos_sin_stock": int(sin_stock)},
        "operaciones": {"movimientos": operaciones, "ingresos": int(ingresos), "salidas": int(salidas)},
        "calidad": {"movimientos_historicos": total, "pendientes": pendiente,
                    "sin_alertas": total - pendiente,
                    "por_tipo": {"saldo": saldo, "fecha": fecha, "area": area, "referencia": referencia},
                    "articulos_digitalizados": digitalizados, "paginas": int(paginas), "lotes": int(cantidad_lotes)},
        "prioridad": [{"articulo_id": a, "nombre": n, "pendientes": p} for a, n, p in prioridad],
        "mensual_moderno": [{"mes": m, "ingresos": mensual.get(m, (0, 0))[0], "salidas": mensual.get(m, (0, 0))[1]} for m in range(1, 13)],
        "recientes": [{"id": id, "articulo": a, "fecha": f, "operacion": o or "Movimiento digital",
                       "ingresos": i or 0, "salidas": s or 0, "operador": u} for id, a, f, o, i, s, u in recientes],
    }
