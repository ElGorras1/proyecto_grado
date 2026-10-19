"""Auditoría de reglas históricas independiente del modelo, sin alterar el Kárdex."""
import csv
import io
import json
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models.kardex import MovimientoKardex
from app.services import reglas_historicas as reglas

router = APIRouter(prefix='/analitica', tags=['Reglas de auditoría histórica'])
lector = require_roles('Administrador', 'Operador', 'Auditor')
Seleccion = Literal['avisos', 'todos', 'sin_avisos', 'insuficiente']


def seleccionadas(db, gestion, articulo, regla, seleccion):
    if regla and regla not in reglas.REGLAS:
        raise HTTPException(422, 'Selecciona una regla histórica válida.')
    return reglas.filtrar(reglas.leer(db, articulo=articulo), gestion=gestion, articulo=articulo,
                          regla=regla, seleccion=seleccion)


@router.get('/reglas-historicas/opciones')
def opciones(db: Session = Depends(get_db), _=Depends(lector)):
    q = db.query(MovimientoKardex).filter(MovimientoKardex.lote_id.isnot(None), MovimientoKardex.estado == 'ACTIVO')
    gestiones = q.with_entities(func.extract('year', MovimientoKardex.fecha_movimiento)).distinct().all()
    return {'gestiones': sorted((int(y) for (y,) in gestiones), reverse=True),
            'politica': reglas.politica(), 'total_historico': q.count()}


@router.get('/reglas-historicas')
def consultar(
    gestion: int | None = Query(None, ge=1900, le=9999),
    articulo: str | None = Query(None, max_length=150),
    regla: str | None = Query(None, max_length=50), seleccion: Seleccion = 'avisos',
    pagina: int = Query(1, ge=1), limite: int = Query(30, ge=1, le=100),
    db: Session = Depends(get_db), _=Depends(lector),
):
    filas = seleccionadas(db, gestion, articulo, regla, seleccion)
    inicio = (pagina-1)*limite
    return {'total': len(filas), 'pagina': pagina, 'limite': limite,
            'resumen': reglas.resumen(filas), 'politica': reglas.politica(),
            'filas': filas[inicio:inicio+limite]}


def celda(v):
    value = '' if v is None else str(v)
    return "'" + value if value.startswith(('=', '+', '-', '@', '\t', '\r', '\n')) else value


@router.get('/reglas-historicas.csv')
def descargar(
    gestion: int | None = Query(None, ge=1900, le=9999),
    articulo: str | None = Query(None, max_length=150),
    regla: str | None = Query(None, max_length=50), seleccion: Seleccion = 'avisos',
    db: Session = Depends(get_db), _=Depends(lector),
):
    filas = seleccionadas(db, gestion, articulo, regla, seleccion)
    out = io.StringIO()
    writer = csv.writer(out, delimiter=';')
    writer.writerow(('ID', 'Gestion para consulta', 'Fecha', 'Fecha estimada', 'Articulo', 'Codigo',
                     'Tanda', 'Lote', 'Foto', 'Fila', 'Ingresos', 'Salidas', 'Saldo previo',
                     'Base utilizable', 'Saldo vigente', 'Esperado por reglas', 'Reglas',
                     'Motivos', 'Evaluaciones no disponibles', 'Foto respaldo', 'Politica'))
    for f in filas:
        writer.writerow([celda(v) for v in (
            f['id'], f['gestion'], f['fecha'], f['fecha_estimada'], f['articulo'], f['codigo'],
            f['tanda'], f['lote_id'], f['numero_pagina'], f['orden_fila'], f['ingresos'], f['salidas'],
            f['saldo_previo'], f['base_utilizable'], f['saldo_vigente'], f['saldo_esperado_reglas'],
            ', '.join(a['codigo'] for a in f['avisos']), ' | '.join(a['mensaje'] for a in f['avisos']),
            json.dumps(f['no_evaluables'], ensure_ascii=False), f['ruta_imagen_respaldo'], reglas.VERSION)])
    return Response('\ufeff'+out.getvalue(), media_type='text/csv; charset=utf-8',
                    headers={'Content-Disposition': f'attachment; filename="reglas_historicas_{gestion or "todas"}.csv"'})


@router.get('/reglas-historicas/{movimiento_id}')
def evidencia(movimiento_id: int, db: Session = Depends(get_db), _=Depends(lector)):
    m = db.get(MovimientoKardex, movimiento_id)
    if m is None or m.lote_id is None or m.estado != "ACTIVO":
        raise HTTPException(404, 'Movimiento histórico activo no encontrado.')
    filas = reglas.leer(db, articulo_id=m.articulo_id)
    fila = next((f for f in filas if f['id'] == movimiento_id), None)
    if fila is None:
        raise HTTPException(404, 'Movimiento histórico activo no encontrado.')
    articulo = [f for f in filas if f['articulo_id'] == fila['articulo_id']]
    posicion = next(i for i, f in enumerate(articulo) if f['id'] == movimiento_id)
    return {'fila': fila, 'politica': reglas.politica(), 'datos_originales': m.datos_originales,
            'vecinos': articulo[max(0, posicion-3):posicion+4]}
