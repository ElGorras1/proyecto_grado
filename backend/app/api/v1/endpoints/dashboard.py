from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy import case, distinct, func, or_
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.activos import Activo
from app.models.kardex import MovimientoKardex as M, LoteCarga
from app.services.calidad_kardex import pendiente_hil_sql
from app.services.clasificador_nodos import ESTADOS_AREA_PENDIENTES

router = APIRouter(prefix="/reportes", tags=["Reportes"])


@router.get("/dashboard")
def resumen_dashboard(gestion: int = Query(..., ge=1900, le=2100),
                      db: Session = Depends(get_db), _usuario=Depends(get_current_user)):
    activo = M.estado == "ACTIVO"
    historico = M.lote_id.isnot(None)
    pendientes = pendiente_hil_sql()
    cantidad_articulos = db.query(func.count(Activo.id)).scalar()
    ultimos = db.query(M.articulo_id, func.max(M.id).label("id")).filter(activo).group_by(M.articulo_id).subquery()
    stock, con_movimiento, sin_stock = db.query(
        func.coalesce(func.sum(M.saldo_registrado), 0), func.count(M.id),
        func.coalesce(func.sum(case((M.saldo_registrado <= 0, 1), else_=0)), 0),
    ).join(ultimos, ultimos.c.id == M.id).one()
    calidad = db.query(
        func.count(M.id),
        func.coalesce(func.sum(case((pendientes, 1), else_=0)), 0),
        func.coalesce(func.sum(case((M.tiene_error_saldo.is_(True), 1), else_=0)), 0),
        func.coalesce(func.sum(case((M.fecha_estado == "PENDIENTE_HIL", 1), else_=0)), 0),
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
