"""Cotejo de operaciones sin exponer el resultado del modelo durante la revisión."""

from collections import defaultdict
from datetime import UTC, datetime
from secrets import randbelow
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.config import settings
from app.db.session import get_db
from app.models.activos import Activo
from app.models.area import Area
from app.models.documento_operativo import DocumentoOperativo
from app.models.analitica_operativa import ModeloOperativo, ResultadoOperativo
from app.models.validacion_operativa import CotejoOperativo, EstudioOperativo
from app.services.inventario import auditar
from app.services.validacion_operativa import en_gestion, muestrear, resumen

router = APIRouter(prefix="/validacion-operativa", tags=["Cotejo de operaciones"])
revisor = require_roles("Administrador", "Auditor")
admin = require_roles("Administrador")
CAMPOS_EVIDENCIA = (
    "clase", "id", "tipo", "cantidad", "direccion", "ocurrido_en", "registrado_en", "documento",
    "area_origen_id", "area_destino_id", "saldo_registrado",
)


class Crear(BaseModel):
    gestion: int = Field(ge=1900, le=9998)
    limite: int = Field(default=50, ge=2, le=200)


class Dictamen(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    etiqueta: Literal["ANOMALO", "NORMAL", "INDETERMINADO"]
    motivo: str = Field(min_length=10, max_length=2000)
    respaldo: str | None = Field(default=None, max_length=250)

    @field_validator("respaldo", mode="after")
    @classmethod
    def normalizar_respaldo(cls, valor):
        return valor or None

    @model_validator(mode="after")
    def comprobar_respaldo(self):
        if self.etiqueta != "INDETERMINADO" and not self.respaldo:
            raise ValueError("Indica el respaldo que permite confirmar este dictamen.")
        return self


def cabecera(e):
    return dict(
        id=e.id, modelo_id=e.modelo_id, gestion=e.gestion, simulado=e.simulado, poblacion=e.poblacion,
        creado_en=e.creado_en,
    )


def publico(caso):
    return dict(id=caso.id, evidencia=caso.evidencia, etiqueta=caso.etiqueta,
                motivo=caso.motivo, respaldo=caso.respaldo, revisor_id=caso.revisor_id,
                revisado_en=caso.revisado_en)


@router.get("")
def listar(db: Session = Depends(get_db), _=Depends(revisor)):
    return dict(
        simulacion=settings.DATOS_OPERATIVOS_SIMULADOS,
        estudios=[cabecera(e) for e in db.query(EstudioOperativo).order_by(EstudioOperativo.id.desc())],
    )


@router.post("", status_code=201)
def crear(payload: Crear, request: Request, db: Session = Depends(get_db), usuario=Depends(admin)):
    modelo = db.query(ModeloOperativo).filter_by(activo=1, estado="COMPLETADO").first()
    if not modelo:
        raise HTTPException(409, "Se requiere un modelo operativo activo para preparar la muestra.")
    consulta = db.query(ResultadoOperativo).filter_by(modelo_id=modelo.id)
    resultados = en_gestion(consulta, payload.gestion).order_by(ResultadoOperativo.id).all()
    semilla = randbelow(2**31)
    muestra = muestrear(resultados, payload.limite, semilla)
    if not muestra:
        raise HTTPException(422, "Esta versión necesita operaciones puntuadas con y sin alerta en la gestión.")
    estudio = EstudioOperativo(modelo_id=modelo.id, creador_id=usuario.id, gestion=payload.gestion,
                               simulado=settings.DATOS_OPERATIVOS_SIMULADOS, poblacion=len(resultados),
                               semilla=semilla)
    db.add(estudio)
    db.flush()
    articulos = {r.articulo_id for r in muestra}
    nombres = dict(db.query(Activo.id, Activo.nombre).filter(Activo.id.in_(articulos)).all())
    areas = dict(db.query(Area.id, Area.nombre).all())
    claves_documentos = {(r.articulo_id, r.snapshot.get("documento")) for r in muestra}
    adjuntos = defaultdict(list)
    for d in db.query(DocumentoOperativo).filter(DocumentoOperativo.articulo_id.in_(articulos)):
        clave = (d.articulo_id, d.referencia)
        if clave in claves_documentos:
            adjuntos[clave].append({"id": d.id, "nombre": d.nombre})
    for resultado in muestra:
        evidencia = {campo: resultado.snapshot.get(campo) for campo in CAMPOS_EVIDENCIA}
        origen = areas.get(evidencia.pop("area_origen_id"))
        destino = areas.get(evidencia.pop("area_destino_id"))
        # En un ingreso directo la ubicación registrada recibe las unidades.
        if evidencia["clase"] == "MOVIMIENTO" and evidencia["direccion"] == "INGRESO":
            origen, destino = None, origen
        evidencia.update(
            articulo_id=resultado.articulo_id, articulo=nombres[resultado.articulo_id],
            area_origen=origen, area_destino=destino,
            adjuntos=adjuntos[(resultado.articulo_id, evidencia["documento"])],
        )
        db.add(CotejoOperativo(estudio_id=estudio.id, resultado_id=resultado.id,
                             prediccion=resultado.alerta, evidencia=evidencia))
    auditar(db, usuario, request, "crear_estudio_operativo", "estudio_operativo", estudio.id,
            {"modelo_id": modelo.id, "gestion": estudio.gestion, "simulado": estudio.simulado,
             "poblacion": estudio.poblacion, "muestra": len(muestra)})
    db.commit()
    return cabecera(estudio)


@router.get("/{estudio_id}")
def consultar(estudio_id: int, db: Session = Depends(get_db), _=Depends(revisor)):
    estudio = db.get(EstudioOperativo, estudio_id)
    if estudio is None:
        raise HTTPException(404, "Estudio no encontrado.")
    casos = db.query(CotejoOperativo).filter_by(estudio_id=estudio.id).order_by(CotejoOperativo.id).all()
    return cabecera(estudio) | resumen(casos) | {"casos": [publico(c) for c in casos]}


@router.post("/{estudio_id}/casos/{caso_id}")
def cotejar(estudio_id: int, caso_id: int, payload: Dictamen, request: Request,
            db: Session = Depends(get_db), usuario=Depends(revisor)):
    consulta = db.query(CotejoOperativo).filter_by(id=caso_id, estudio_id=estudio_id)
    caso = consulta.first()
    if caso is None:
        raise HTTPException(404, "Caso no encontrado en este estudio.")
    dictamen = payload.model_dump()
    actualizado = consulta.filter(CotejoOperativo.etiqueta.is_(None)).update(
        dictamen | {"revisor_id": usuario.id, "revisado_en": datetime.now(UTC)},
        synchronize_session=False,
    )
    if not actualizado:
        db.refresh(caso)
        if caso.revisor_id == usuario.id and all(getattr(caso, k) == v for k, v in dictamen.items()):
            return publico(caso)
        raise HTTPException(409, "Este caso ya tiene un dictamen conservado.")
    auditar(db, usuario, request, "cotejar_operacion", "cotejo_operativo", caso.id,
            {"estudio_id": estudio_id, **dictamen})
    db.commit()
    return publico(caso)
