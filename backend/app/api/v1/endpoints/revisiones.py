"""Bandeja común: conserva el origen y la decisión propia de cada aviso."""

from collections import Counter
from typing import Literal
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, defer
from app.api.deps import require_roles
from app.db.session import get_db
from app.models.activos import Activo
from app.models.auditoria_historica import ResultadoHistorico
from app.models.automatizacion_analitica import PoliticaAnalitica, ResultadoSeguimiento
from app.models.control_alertas import CasoControl
from app.models.kardex import MovimientoKardex
from app.services.automatizacion_analitica import modelo_referencia, elegibles_del_corte
from app.services.calidad_kardex import pendiente_hil_sql
from app.services.datos_analitica import huella, leer_corte
from app.services.fechas_documentales import fecha_asignable
from app.services.tratamiento_hil import resumen_tratamiento

router = APIRouter(prefix="/revisiones", tags=["Revisiones y alertas"])
lector = require_roles("Administrador", "Auditor", "Operador")
ABIERTOS = ("PENDIENTE", "EN_REVISION", "REQUIERE_SEGUIMIENTO")


@router.get("/pendientes")
def pendientes(
    origen: Literal["TODOS", "HIL", "MODELO", "OPERATIVO"] = "TODOS",
    gestion: int | None = Query(None, ge=1900, le=9998),
    sin_fecha: bool = False,
    articulo: str = Query("", max_length=150),
    incluir_tratados: bool = False,
    pagina: int = Query(1, ge=1),
    limite: int = Query(30, ge=1, le=100),
    db: Session = Depends(get_db),
    _=Depends(lector),
):
    if sin_fecha and gestion is not None:
        raise HTTPException(422, "Selecciona una gestión o los documentos sin fecha completa.")
    filas = []
    for m, a in (
        db.query(MovimientoKardex, Activo)
        .options(defer(MovimientoKardex.datos_originales))
        .join(Activo, Activo.id == MovimientoKardex.articulo_id)
        .filter(
            MovimientoKardex.estado == "ACTIVO",
            MovimientoKardex.lote_id.isnot(None),
            pendiente_hil_sql(),
        )
    ):
        tratamiento = resumen_tratamiento(m)
        if not incluir_tratados and tratamiento["estado"] == "CATEGORIZADO_CON_MARCA":
            continue
        filas.append(
            dict(
                tipo="HIL",
                origen="HIL",
                id=m.id,
                articulo_id=a.id,
                articulo=a.nombre,
                codigo=a.codigo,
                fecha=m.fecha_movimiento.isoformat() if fecha_asignable(m) else None,
                descripcion=m.detalle,
                estado=tratamiento["etiqueta"],
                prioridad="ALTA" if m.tiene_error_saldo else "MEDIA",
                score=None,
                destino=dict(path="/kardex-digital", query={"articulo_id": a.id, "tab": "hil"}),
            )
        )
    modelo = modelo_referencia(db)
    if modelo:
        nuevos = list(db.query(ResultadoSeguimiento).filter_by(modelo_id=modelo.id))
        actuales = {}
        if nuevos:
            p = db.get(PoliticaAnalitica, 1)
            corte = leer_corte(db)
            hashes = {
                f["id"]: huella(f)
                for f in elegibles_del_corte(corte, p.gestion_hasta if p else 2025)
            }
            actuales = {
                r.movimiento_id: r
                for r in nuevos
                if hashes.get(r.movimiento_id) == r.huella_snapshot
            }
        for r in db.query(ResultadoHistorico).filter(
            ResultadoHistorico.modelo_id == modelo.id,
            ResultadoHistorico.alerta.is_(True),
            ResultadoHistorico.estado_revision.in_(ABIERTOS),
        ):
            if r.movimiento_id in actuales:
                continue
            f = r.snapshot
            filas.append(
                dict(
                    tipo="HISTORICO",
                    origen="MODELO",
                    id=r.id,
                    articulo_id=r.articulo_id,
                    articulo=f["articulo"],
                    codigo=f["codigo"],
                    fecha=f["fecha"],
                    descripcion=f["detalle"],
                    estado=r.estado_revision,
                    prioridad="MEDIA",
                    score=r.score,
                    destino=dict(
                        path="/analitica",
                        query={"modelo": modelo.id, "resultado_id": r.id, "gestion": r.gestion},
                    ),
                )
            )
        for r in actuales.values():
            if not r.alerta or r.estado_revision not in ABIERTOS:
                continue
            f = r.snapshot
            filas.append(
                dict(
                    tipo="SEGUIMIENTO",
                    origen="MODELO",
                    id=r.id,
                    articulo_id=r.articulo_id,
                    articulo=f["articulo"],
                    codigo=f["codigo"],
                    fecha=f["fecha"],
                    descripcion=f["detalle"],
                    estado=r.estado_revision,
                    prioridad="MEDIA",
                    score=r.score,
                    destino=None,
                )
            )
    for c, a in (
        db.query(CasoControl, Activo)
        .join(Activo, Activo.id == CasoControl.articulo_id)
        .filter(CasoControl.estado.in_(("PENDIENTE", "EN_REVISION", "SEGUIMIENTO")))
    ):
        creado = (
            c.creado_en.replace(tzinfo=ZoneInfo("UTC"))
            if c.creado_en.tzinfo is None
            else c.creado_en
        )
        filas.append(
            dict(
                tipo="OPERATIVO",
                origen="OPERATIVO",
                id=c.id,
                articulo_id=a.id,
                articulo=a.nombre,
                codigo=a.codigo,
                fecha=creado.astimezone(ZoneInfo("America/La_Paz")).date().isoformat(),
                descripcion=" · ".join(c.codigos),
                estado=c.estado,
                prioridad=c.prioridad,
                score=None,
                destino=dict(
                    path="/alertas-inventario",
                    query={"caso_id": c.id, "articulo_id": c.articulo_id},
                ),
            )
        )
    gestiones = sorted({int(f["fecha"][:4]) for f in filas if f["fecha"]}, reverse=True)
    termino = articulo.strip().casefold()
    filtradas = [
        f
        for f in filas
        if (not termino or termino in (f["articulo"] + " " + f["codigo"]).casefold())
        and (not sin_fecha or f["fecha"] is None)
        and (gestion is None or f["fecha"] and int(f["fecha"][:4]) == gestion)
    ]
    conteos = Counter(f["origen"] for f in filtradas)
    filtradas = [f for f in filtradas if origen == "TODOS" or f["origen"] == origen]
    filtradas.sort(
        key=lambda f: (
            {"ALTA": 0, "MEDIA": 1, "BAJA": 2}[f["prioridad"]],
            -(f["score"] or 0),
            -(int(f["fecha"].replace("-", "")[:8]) if f["fecha"] else 0),
            f["tipo"],
            f["id"],
        )
    )
    inicio = (pagina - 1) * limite
    return dict(
        total=len(filtradas),
        pagina=pagina,
        limite=limite,
        conteos={k: conteos[k] for k in ("HIL", "MODELO", "OPERATIVO")},
        gestiones=gestiones,
        filas=filtradas[inicio : inicio + limite],
        modelo_base_id=modelo.id if modelo else None,
        alcance="Son avisos para revisar, no discrepancias confirmadas. Un movimiento puede tener avisos de distinto origen. Los casos HIL ya categorizados se conservan y se muestran solo al solicitarlos.",
    )
