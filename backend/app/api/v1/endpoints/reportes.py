"""Reportes de movimientos por gestión; no infieren existencias de cierre."""

import csv
import io
from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import case, distinct, func, or_
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.activos import Activo
from app.models.kardex import MovimientoKardex
from app.services.clasificador_nodos import ESTADOS_AREA_PENDIENTES
from app.services.calidad_kardex import pendiente_hil_sql, tipos_alerta

router = APIRouter(prefix="/reportes", tags=["Reportes"])


def _pendiente_hil():
    return pendiente_hil_sql()


def _consulta(db, gestion, mes, articulo, origen, direccion, nodo, revision):
    inicio = date(gestion, mes or 1, 1)
    fin = date(gestion + 1, 1, 1) if not mes or mes == 12 else date(gestion, mes + 1, 1)
    consulta = db.query(MovimientoKardex, Activo).join(
        Activo, Activo.id == MovimientoKardex.articulo_id
    ).filter(
        MovimientoKardex.fecha_movimiento >= inicio,
        MovimientoKardex.fecha_movimiento < fin,
        MovimientoKardex.estado == "ACTIVO",
    )
    if articulo:
        termino = f"%{articulo.strip()}%"
        consulta = consulta.filter(or_(Activo.nombre.ilike(termino), Activo.codigo.ilike(termino)))
    if origen == "historico":
        consulta = consulta.filter(MovimientoKardex.lote_id.isnot(None))
    elif origen == "moderno":
        consulta = consulta.filter(MovimientoKardex.lote_id.is_(None))
    if direccion == "ingreso":
        consulta = consulta.filter(MovimientoKardex.ingresos > 0)
    elif direccion == "salida":
        consulta = consulta.filter(MovimientoKardex.salidas > 0)
    if nodo:
        consulta = consulta.filter(MovimientoKardex.nodo_grafo == nodo)
    if revision == "pendiente":
        consulta = consulta.filter(_pendiente_hil())
    elif revision == "sin_alertas":
        consulta = consulta.filter(~_pendiente_hil())
    return consulta


def _fila(mov, activo):
    rev = mov.revision_documental or {}
    return {
        "id": mov.id,
        "fecha": mov.fecha_movimiento.isoformat(),
        "fecha_original": mov.fecha_original.isoformat() if mov.fecha_original else None,
        "fecha_estado": mov.fecha_estado,
        "tipos_alerta": tipos_alerta(mov),
        "articulo": activo.nombre,
        "codigo": activo.codigo,
        "origen": "Histórico" if mov.lote_id is not None else "Moderno",
        "lote_id": mov.lote_id,
        "pagina": mov.numero_pagina,
        "orden_fila": mov.orden_fila,
        "detalle": mov.detalle,
        "referencia": mov.referencia,
        "area_original": mov.area,
        "nodo": mov.nodo_grafo,
        "tipo_operacion": mov.tipo_operacion,
        "ingresos": mov.ingresos or 0,
        "salidas": mov.salidas or 0,
        "pendiente_hil": bool(tipos_alerta(mov)),
        "origen_fecha": rev.get("origen_fecha", "SIN_REVISION_DOCUMENTAL"),
        "origen_saldo": rev.get("origen_saldo", "SIN_REVISION_DOCUMENTAL"),
        "saldo_documental": rev.get("saldo_documental"),
        "saldo_vigente": mov.saldo_registrado,
        "saldo_esperado": mov.saldo_calculado,
        "hallazgos_documentales": ", ".join(rev.get("hallazgos", [])),
    }


@router.get("/inventario/opciones")
def opciones_reporte(
    db: Session = Depends(get_db),
    _usuario=Depends(get_current_user),
):
    activos = MovimientoKardex.estado == "ACTIVO"
    fechas = db.query(MovimientoKardex.fecha_movimiento).filter(activos).distinct().all()
    nodos = db.query(distinct(MovimientoKardex.nodo_grafo)).filter(
        activos, MovimientoKardex.nodo_grafo.isnot(None)
    ).all()
    return {
        "gestiones": sorted({fecha.year for (fecha,) in fechas if fecha}, reverse=True),
        "nodos": sorted(n[0] for n in nodos if n[0]),
    }


@router.get("/inventario")
def reporte_inventario(
    gestion: int = Query(..., ge=1900, le=2100),
    mes: int | None = Query(None, ge=1, le=12),
    articulo: str | None = Query(None, max_length=150),
    origen: Literal["todos", "historico", "moderno"] = "todos",
    direccion: Literal["todas", "ingreso", "salida"] = "todas",
    nodo: str | None = Query(None, max_length=100),
    revision: Literal["todas", "pendiente", "sin_alertas"] = "todas",
    pagina: int = Query(1, ge=1),
    limite: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    _usuario=Depends(get_current_user),
):
    consulta = _consulta(db, gestion, mes, articulo, origen, direccion, nodo, revision)
    subconsulta = consulta.with_entities(
        MovimientoKardex.id.label("id"),
        MovimientoKardex.articulo_id.label("articulo_id"),
        MovimientoKardex.fecha_movimiento.label("fecha"),
        MovimientoKardex.ingresos.label("ingresos"),
        MovimientoKardex.salidas.label("salidas"),
        MovimientoKardex.lote_id.label("lote_id"),
        case((_pendiente_hil(), 1), else_=0).label("pendiente"),
    ).subquery()
    total, articulos, ingresos, salidas, pendientes, historicos, modernos = db.query(
        func.count(subconsulta.c.id),
        func.count(distinct(subconsulta.c.articulo_id)),
        func.coalesce(func.sum(subconsulta.c.ingresos), 0),
        func.coalesce(func.sum(subconsulta.c.salidas), 0),
        func.coalesce(func.sum(subconsulta.c.pendiente), 0),
        func.coalesce(func.sum(case((subconsulta.c.lote_id.isnot(None), 1), else_=0)), 0),
        func.coalesce(func.sum(case((subconsulta.c.lote_id.is_(None), 1), else_=0)), 0),
    ).one()
    por_mes = db.query(
        func.extract("month", subconsulta.c.fecha),
        func.count(subconsulta.c.id),
        func.coalesce(func.sum(subconsulta.c.ingresos), 0),
        func.coalesce(func.sum(subconsulta.c.salidas), 0),
    ).group_by(func.extract("month", subconsulta.c.fecha)).all()
    meses = {int(m): (int(c), int(i), int(s)) for m, c, i, s in por_mes}
    filas = consulta.order_by(
        MovimientoKardex.fecha_movimiento.asc(), MovimientoKardex.id.asc()
    ).offset((pagina - 1) * limite).limit(limite).all()
    return {
        "gestion": gestion,
        "resumen": {
            "movimientos": total,
            "articulos": articulos,
            "ingresos": int(ingresos),
            "salidas": int(salidas),
            "pendientes_hil": int(pendientes),
            "historicos": int(historicos),
            "modernos": int(modernos),
        },
        "mensual": [
            {"mes": n, "movimientos": meses.get(n, (0, 0, 0))[0],
             "ingresos": meses.get(n, (0, 0, 0))[1],
             "salidas": meses.get(n, (0, 0, 0))[2]}
            for n in range(1, 13)
        ],
        "pagina": pagina,
        "limite": limite,
        "filas": [_fila(mov, activo) for mov, activo in filas],
    }


def _celda_csv(valor):
    texto = "" if valor is None else str(valor)
    # Excel interpreta estos prefijos como fórmulas; el Kárdex contiene texto no confiable.
    if texto.startswith(("=", "+", "-", "@", "\t", "\r", "\n")):
        return "'" + texto
    return texto


@router.get("/inventario.csv")
def exportar_inventario(
    gestion: int = Query(..., ge=1900, le=2100),
    mes: int | None = Query(None, ge=1, le=12),
    articulo: str | None = Query(None, max_length=150),
    origen: Literal["todos", "historico", "moderno"] = "todos",
    direccion: Literal["todas", "ingreso", "salida"] = "todas",
    nodo: str | None = Query(None, max_length=100),
    revision: Literal["todas", "pendiente", "sin_alertas"] = "todas",
    db: Session = Depends(get_db),
    _usuario=Depends(get_current_user),
):
    consulta = _consulta(db, gestion, mes, articulo, origen, direccion, nodo, revision)

    def generar():
        yield "\ufeff"
        buffer = io.StringIO()
        escritor = csv.writer(buffer, delimiter=";")
        escritor.writerow([
            "ID", "Fecha para consulta", "Fecha original", "Estado fecha", "Código", "Artículo", "Origen", "Lote",
            "Página", "Fila", "Detalle", "Referencia", "Área original", "Nodo",
            "Tipo de operación", "Ingresos", "Salidas", "Pendiente HIL",
            "Origen fecha", "Origen saldo", "Saldo documental cotejado", "Saldo vigente", "Saldo esperado", "Hallazgos conservados",
        ])
        yield buffer.getvalue()
        buffer.seek(0)
        buffer.truncate(0)
        for mov, activo in consulta.order_by(MovimientoKardex.id).yield_per(500):
            fila = _fila(mov, activo)
            escritor.writerow([_celda_csv(fila[clave]) for clave in (
                "id", "fecha", "fecha_original", "fecha_estado", "codigo", "articulo", "origen", "lote_id",
                "pagina", "orden_fila", "detalle", "referencia", "area_original", "nodo",
                "tipo_operacion", "ingresos", "salidas", "pendiente_hil",
                "origen_fecha", "origen_saldo", "saldo_documental", "saldo_vigente", "saldo_esperado", "hallazgos_documentales",
            )])
            yield buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)

    return StreamingResponse(
        generar(), media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="reporte_inventario_{gestion}.csv"'},
    )
