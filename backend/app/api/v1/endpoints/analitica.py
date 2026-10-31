"""API de auditoría retrospectiva. Nunca modifica movimientos."""

import csv
import io
from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import Response
from sqlalchemy import case
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models.activos import Activo
from app.models.auditoria_historica import ModeloHistorico, ResultadoHistorico, RevisionHistorica
from app.models.kardex import MovimientoKardex
from app.models.usuario import Usuario
from app.schemas.analitica import EntrenamientoHistorico, RevisionAnalitica
from app.services.datos_analitica import huella, leer_corte, snapshot
from app.services.evaluacion_analitica import diagnosticar
from app.services.evaluacion_temporal import preparar_corte_temporal
from app.services.trabajador_analitica import evento
from app.services.resumen_gestiones import resumir_gestiones
from app.api.v1.endpoints.reportes import _celda_csv

router = APIRouter(prefix="/analitica", tags=["Auditoría histórica"])
lector = require_roles("Administrador", "Operador", "Auditor")
administrador = require_roles("Administrador")
auditor = require_roles("Administrador", "Auditor")


def obtener(db, clase, id):
    obj = db.get(clase, id)
    if obj is None:
        raise HTTPException(404, "Registro no encontrado")
    return obj


def modelo_publico(m):
    return {
        "id": m.id,
        "estado": m.estado,
        "creado_en": m.creado_en,
        "terminado_en": m.terminado_en,
        "configuracion": m.configuracion,
        "perfil": m.corte["perfil"],
        "huella": m.huella,
        "metricas": m.metricas,
        "umbral": m.umbral,
        "error": m.error,
    }


def resultado_publico(r):
    return {
        k: getattr(r, k)
        for k in (
            "id",
            "modelo_id",
            "movimiento_id",
            "gestion",
            "articulo_id",
            "nodo",
            "score",
            "alerta",
            "particion",
            "muestra_control",
            "snapshot",
            "contexto",
            "estado_revision",
            "revision_numero",
            "etiqueta",
        )
    }


@router.get("/perfil")
def perfil(db: Session = Depends(get_db), _=Depends(lector)):
    corte = leer_corte(db)
    return {**corte["perfil"], "huella": huella(corte["filas"])}


@router.post("/entrenar", status_code=202)
def entrenar(
    config: EntrenamientoHistorico,
    request: Request,
    db: Session = Depends(get_db),
    usuario=Depends(administrador),
):
    if db.query(ModeloHistorico).filter(ModeloHistorico.plaza == 1).first():
        raise HTTPException(409, "Ya hay un entrenamiento pendiente o en ejecución.")
    if config.excluir_articulos:
        encontrados = db.query(Activo.id).filter(Activo.id.in_(config.excluir_articulos)).count()
        if encontrados != len(set(config.excluir_articulos)):
            raise HTTPException(422, "Hay artículos excluidos que no existen.")
    corte = leer_corte(db, config.excluir_articulos)
    if config.modo == "TEMPORAL":
        corte = preparar_corte_temporal(corte, config.gestion_evaluacion)
        if not corte["temporal"]["suficiente"]:
            raise HTTPException(
                422, {"mensaje": "Muestra temporal insuficiente.", "plan": corte["temporal"]}
            )
    j = ModeloHistorico(
        id=str(uuid4()),
        estado="PENDIENTE",
        plaza=1,
        usuario_id=usuario.id,
        configuracion=config.model_dump(),
        corte=corte,
        huella=huella(corte["filas"]),
    )
    db.add(j)
    evento(
        db,
        usuario.id,
        "ANALITICA_SOLICITADA",
        j.id,
        {"configuracion": j.configuracion, "elegibles": corte["perfil"]["elegibles"]},
        request.client.host if request.client else None,
    )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Otro usuario acaba de iniciar un entrenamiento.")
    return {"job_id": j.id, "estado": j.estado}


@router.get("/temporal/plan")
def plan_temporal(
    gestion_evaluacion: int = Query(..., ge=1902, le=9998),
    excluir_articulos: list[int] = Query(default=[]),
    db: Session = Depends(get_db),
    _=Depends(lector),
):
    from datetime import datetime
    from zoneinfo import ZoneInfo

    if gestion_evaluacion >= datetime.now(ZoneInfo("America/La_Paz")).year:
        raise HTTPException(422, "Selecciona un año documental ya concluido.")
    if len(excluir_articulos) > 400:
        raise HTTPException(422, "Demasiados artículos excluidos.")
    if excluir_articulos and db.query(Activo.id).filter(
        Activo.id.in_(excluir_articulos)
    ).count() != len(set(excluir_articulos)):
        raise HTTPException(422, "Hay artículos excluidos que no existen.")
    corte = preparar_corte_temporal(leer_corte(db, excluir_articulos), gestion_evaluacion)
    return corte["temporal"]


@router.get("/modelos")
def modelos(
    pagina: int = Query(1, ge=1),
    limite: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _=Depends(lector),
):
    q = db.query(ModeloHistorico)
    return {
        "total": q.count(),
        "filas": [
            modelo_publico(m)
            for m in q.order_by(ModeloHistorico.creado_en.desc(), ModeloHistorico.id)
            .offset((pagina - 1) * limite)
            .limit(limite)
        ],
    }


@router.get("/modelos/{modelo_id}")
def modelo(modelo_id: str, db: Session = Depends(get_db), _=Depends(lector)):
    m = obtener(db, ModeloHistorico, modelo_id)
    corte = leer_corte(db, m.configuracion["excluir_articulos"])
    return {**modelo_publico(m), "datos_cambiaron": huella(corte["filas"]) != m.huella}


@router.get("/modelos/{modelo_id}/evaluacion")
def evaluacion(modelo_id: str, db: Session = Depends(get_db), _=Depends(lector)):
    m = obtener(db, ModeloHistorico, modelo_id)
    filas = db.query(ResultadoHistorico).filter_by(modelo_id=m.id).all()
    return diagnosticar(m, filas)["evaluacion"]


@router.get("/modelos/{modelo_id}/gestiones")
def gestiones(modelo_id: str, db: Session = Depends(get_db), _=Depends(lector)):
    return resumir_gestiones(db, obtener(db, ModeloHistorico, modelo_id))


@router.get("/modelos/{modelo_id}/diagnostico")
def diagnostico(modelo_id: str, db: Session = Depends(get_db), _=Depends(lector)):
    m = obtener(db, ModeloHistorico, modelo_id)
    filas = db.query(ResultadoHistorico).filter_by(modelo_id=m.id).all()
    return diagnosticar(m, filas)


@router.get("/resultados")
def resultados(
    modelo_id: str,
    gestion: int | None = Query(None, ge=1, le=9999),
    articulo: str | None = Query(None, max_length=150),
    articulo_id: int | None = Query(None, gt=0),
    nodo: str | None = Query(None, max_length=100),
    estado: (
        Literal["PENDIENTE", "EN_REVISION", "JUSTIFICADO", "REQUIERE_SEGUIMIENTO", "CERRADO"] | None
    ) = None,
    seleccion: Literal["todos", "alertas", "control", "top_modelo", "top_regla"] = "todos",
    pagina: int = Query(1, ge=1),
    limite: int = Query(30, ge=1, le=100),
    db: Session = Depends(get_db),
    _=Depends(lector),
):
    m = obtener(db, ModeloHistorico, modelo_id)
    q = consulta_resultados(db, m, gestion, articulo, articulo_id, nodo, estado, seleccion)
    return {
        "total": q.count(),
        "pagina": pagina,
        "filas": [resultado_publico(r) for r in q.offset((pagina - 1) * limite).limit(limite)],
    }


def consulta_resultados(db, m, gestion, articulo, articulo_id, nodo, estado, seleccion):
    """La lista y el archivo comparten filtros, nombres del corte y orden estable."""
    q = db.query(ResultadoHistorico).filter_by(modelo_id=m.id)
    if articulo_id is not None:
        q = q.filter_by(articulo_id=articulo_id)
    if gestion is not None:
        q = q.filter_by(gestion=gestion)
    if nodo:
        q = q.filter_by(nodo=nodo)
    if estado:
        q = q.filter_by(estado_revision=estado)
    if articulo:
        # Buscar sobre el corte, no sobre nombres que pudieron cambiar.
        ids = [
            f["articulo_id"]
            for f in m.corte["filas"]
            if articulo.casefold() in (f["articulo"] + " " + f["codigo"]).casefold()
        ]
        q = q.filter(ResultadoHistorico.articulo_id.in_(set(ids)))
    orden = ResultadoHistorico.score.desc()
    if seleccion == "alertas":
        q = q.filter_by(alerta=True)
    elif seleccion == "control":
        q = q.filter_by(muestra_control=True)
    elif seleccion in ("top_modelo", "top_regla"):
        clave = "top_evaluacion" if seleccion == "top_modelo" else "top_regla"
        ids_ordenados = (m.metricas or {}).get(clave, [])
        q = q.filter(ResultadoHistorico.movimiento_id.in_(ids_ordenados))
        if ids_ordenados:
            orden = case(
                {id: posicion for posicion, id in enumerate(ids_ordenados)},
                value=ResultadoHistorico.movimiento_id,
            )
    return q.order_by(orden, ResultadoHistorico.movimiento_id)


@router.get("/resultados.csv")
def exportar_resultados(
    modelo_id: str,
    gestion: int | None = Query(None, ge=1, le=9999),
    articulo: str | None = Query(None, max_length=150),
    articulo_id: int | None = Query(None, gt=0),
    nodo: str | None = Query(None, max_length=100),
    estado: (
        Literal["PENDIENTE", "EN_REVISION", "JUSTIFICADO", "REQUIERE_SEGUIMIENTO", "CERRADO"] | None
    ) = None,
    seleccion: Literal["todos", "alertas", "control", "top_modelo", "top_regla"] = "todos",
    db: Session = Depends(get_db),
    _=Depends(lector),
):
    m = obtener(db, ModeloHistorico, modelo_id)
    if m.estado != "COMPLETADO":
        raise HTTPException(409, "La descarga requiere un modelo completado.")
    consulta = consulta_resultados(db, m, gestion, articulo, articulo_id, nodo, estado, seleccion)
    buffer = io.StringIO(newline="")
    buffer.write("\ufeff")
    escritor = csv.writer(buffer, delimiter=";")
    escritor.writerow(
        [
            "Modelo",
            "Huella del corte",
            "Modelo creado en",
            "Exportado en UTC",
            "Umbral",
            "Resultado ID",
            "Movimiento ID",
            "Artículo ID",
            "Gestión documental",
            "Código del corte",
            "Artículo del corte",
            "Fecha del corte",
            "Detalle del corte",
            "Nodo del corte",
            "Ingreso",
            "Salida",
            "Puntuación",
            "Aviso estadístico",
            "Partición",
            "Muestra de control",
            "Estado de revisión",
            "Revisión número",
            "Etiqueta de revisión",
            "Lote",
            "Página",
            "Fila",
            "Fotografía del corte",
            "Alcance",
        ]
    )
    exportado = datetime.now(UTC).isoformat()
    # Materializar durante la sesión evita consultar la base después de cerrarla.
    for r in consulta.yield_per(500):
        f = r.snapshot
        escritor.writerow(
            [
                _celda_csv(v)
                for v in [
                    m.id,
                    m.huella,
                    m.creado_en.isoformat(),
                    exportado,
                    m.umbral,
                    r.id,
                    r.movimiento_id,
                    r.articulo_id,
                    r.gestion,
                    f.get("codigo"),
                    f.get("articulo"),
                    f.get("fecha"),
                    f.get("detalle"),
                    r.nodo,
                    f.get("ingresos"),
                    f.get("salidas"),
                    r.score,
                    r.alerta,
                    r.particion,
                    r.muestra_control,
                    r.estado_revision,
                    r.revision_numero,
                    r.etiqueta,
                    f.get("lote_id"),
                    f.get("numero_pagina"),
                    f.get("orden_fila"),
                    f.get("ruta_imagen_respaldo"),
                    "Corte conservado; aviso estadístico, no discrepancia confirmada ni dato vigente",
                ]
            ]
        )
    return Response(
        buffer.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="auditoria_historica_{gestion or "todas"}.csv"'
        },
    )


@router.get("/resultados/{resultado_id}")
def detalle(resultado_id: int, db: Session = Depends(get_db), _=Depends(lector)):
    r = obtener(db, ResultadoHistorico, resultado_id)
    m = obtener(db, ModeloHistorico, r.modelo_id)
    actual = (
        db.query(MovimientoKardex, Activo)
        .join(Activo)
        .filter(MovimientoKardex.id == r.movimiento_id)
        .first()
    )
    actual = snapshot(*actual) if actual else None
    vecinos = sorted(
        [
            f
            for f in m.corte["filas"]
            if f["articulo_id"] == r.articulo_id and f["lote_id"] is not None
        ],
        key=lambda f: (f["lote_id"], f["numero_pagina"] or 0, f["orden_fila"] or 0, f["id"]),
    )
    pos = next(i for i, f in enumerate(vecinos) if f["id"] == r.movimiento_id)
    historial = (
        db.query(RevisionHistorica, Usuario.nombre)
        .join(Usuario)
        .filter(RevisionHistorica.resultado_id == r.id)
        .order_by(RevisionHistorica.id)
        .all()
    )
    return {
        **resultado_publico(r),
        "actual": actual,
        "datos_cambiaron": actual != r.snapshot,
        "vecinos": vecinos[max(0, pos - 2) : pos + 3],
        "revisiones": [
            {
                "id": h.id,
                "usuario": nombre,
                "fecha": h.creado_en,
                "anterior": h.anterior,
                "estado": h.estado,
                "motivo": h.motivo,
                "etiqueta": h.etiqueta,
            }
            for h, nombre in historial
        ],
    }


@router.post("/resultados/{resultado_id}/revision")
def revisar(
    resultado_id: int,
    revision: RevisionAnalitica,
    request: Request,
    db: Session = Depends(get_db),
    usuario=Depends(auditor),
):
    r = obtener(db, ResultadoHistorico, resultado_id)
    anterior = r.estado_revision
    if revision.estado == "JUSTIFICADO" and revision.etiqueta != "LEGITIMO":
        raise HTTPException(422, "Justificado requiere la conclusión Legítimo.")
    if revision.estado == "CERRADO" and revision.etiqueta == "NO_CONCLUYENTE":
        raise HTTPException(
            422, "Un caso no concluyente debe permanecer en revisión o seguimiento."
        )
    actualizados = (
        db.query(ResultadoHistorico)
        .filter(
            ResultadoHistorico.id == r.id,
            ResultadoHistorico.revision_numero == revision.revision_esperada,
        )
        .update(
            {
                "estado_revision": revision.estado,
                "etiqueta": revision.etiqueta,
                "revision_numero": revision.revision_esperada + 1,
            },
            synchronize_session=False,
        )
    )
    if not actualizados:
        db.rollback()
        raise HTTPException(409, "Otra persona revisó este hallazgo. Actualiza el detalle.")
    db.add(
        RevisionHistorica(
            resultado_id=r.id,
            usuario_id=usuario.id,
            anterior=anterior,
            estado=revision.estado,
            motivo=revision.motivo,
            etiqueta=revision.etiqueta,
        )
    )
    evento(
        db,
        usuario.id,
        "ANALITICA_REVISADA",
        r.modelo_id,
        {"resultado_id": r.id, "anterior": anterior, **revision.model_dump()},
        request.client.host if request.client else None,
    )
    db.commit()
    db.refresh(r)
    return resultado_publico(r)
