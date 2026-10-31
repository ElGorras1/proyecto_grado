"""Preparación y referencia humana separadas de HIL y del modelo congelado."""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.crud.auditoria import registrar_evento_auditoria
from app.db.session import get_db
from app.models.auditoria import AuditoriaSistema
from app.services.datos_analitica import huella
from app.services import validacion_independiente as servicio

router = APIRouter(prefix="/validacion", tags=["Validación independiente"])
lector = require_roles("Administrador", "Auditor", "Operador")
revisor = require_roles("Administrador", "Auditor")


class CrearEstudio(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    tipo: Literal["DOCUMENTAL", "DETECTOR"]
    modelo_id: str | None = Field(None, min_length=36, max_length=36)
    tamano: int = Field(100, ge=1, le=5000)
    semilla: str = Field(min_length=1, max_length=80)
    referencia_protocolo: str = Field(min_length=10, max_length=500)

    @model_validator(mode="after")
    def modelo_corresponde(self):
        if (self.tipo == "DETECTOR") != (self.modelo_id is not None):
            raise ValueError("Solo la validación del detector requiere una versión del modelo.")
        return self


class Etiquetar(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    huella_estudio: str = Field(pattern="^[0-9a-f]{64}$")
    revision_esperada: int = Field(ge=0)
    etiqueta: Literal[
        "COINCIDE_DOCUMENTO",
        "DIFERENCIA_DOCUMENTO",
        "INUSUAL_RELEVANTE",
        "LEGITIMO",
        "ERROR_DOCUMENTAL",
        "NO_CONCLUYENTE",
        "NORMAL",
        "ANOMALO",
        "INDETERMINADO",
    ]
    motivo: str = Field(min_length=10, max_length=4000)
    referencia: str = Field(min_length=3, max_length=500)
    independiente: Literal[True]
    segunda_revision: bool = False
    criterio: Literal["CANTIDAD", "FECHA", "TIPO_OPERACION", "AREA", "MULTIPLE"] | None = None


@router.get("/marco")
def marco(
    tipo: Literal["DOCUMENTAL", "DETECTOR"],
    modelo_id: str | None = None,
    db: Session = Depends(get_db),
    _=Depends(lector),
):
    if (tipo == "DETECTOR") != (modelo_id is not None):
        raise HTTPException(422, "Solo el marco del detector requiere una versión del modelo.")
    return servicio.marco(db, tipo, modelo_id)


@router.get("/estudios")
def listar(pagina: int = Query(1, ge=1), db: Session = Depends(get_db), _=Depends(lector)):
    q = db.query(AuditoriaSistema).filter_by(accion=servicio.CREAR, recurso=servicio.RECURSO)
    return dict(
        total=q.count(),
        filas=[
            servicio.cabecera(e)
            for e in q.order_by(AuditoriaSistema.id.desc()).offset((pagina - 1) * 20).limit(20)
        ],
    )


@router.post("/estudios", status_code=201)
def crear(
    payload: CrearEstudio, request: Request, db: Session = Depends(get_db), usuario=Depends(revisor)
):
    datos = servicio.crear_datos(db, **payload.model_dump())
    estudio = registrar_evento_auditoria(
        db,
        usuario_id=usuario.id,
        accion=servicio.CREAR,
        recurso=servicio.RECURSO,
        recurso_id=None,
        resultado="exito",
        ip_origen=request.client.host if request.client else None,
        detalle=datos,
    )
    return servicio.cabecera(estudio)


@router.get("/estudios/{estudio_id}")
def detalle(estudio_id: int, db: Session = Depends(get_db), usuario=Depends(lector)):
    return servicio.detalle_publico(db, servicio.obtener(db, estudio_id), usuario)


@router.get("/estudios/{estudio_id}/informe.json")
def informe(estudio_id: int, db: Session = Depends(get_db), _=Depends(lector)):
    datos = jsonable_encoder(servicio.informe(db, servicio.obtener(db, estudio_id)))
    datos["huella_exportacion"] = huella(datos)
    return JSONResponse(
        datos,
        headers={"Content-Disposition": f'attachment; filename="Validacion_{estudio_id}.json"'},
    )


@router.post("/estudios/{estudio_id}/filas/{item_id}/etiqueta")
def etiquetar(
    estudio_id: int,
    item_id: int,
    payload: Etiquetar,
    request: Request,
    db: Session = Depends(get_db),
    usuario=Depends(revisor),
):
    estudio = servicio.obtener(db, estudio_id, bloquear=True)
    d = estudio.detalle
    if usuario.id in {estudio.usuario_id, d["entrenador_id"]}:
        raise HTTPException(
            403,
            "La revisión corresponde a otra persona: quien preparó el estudio o entrenó el modelo no puede etiquetarlo.",
        )
    if payload.huella_estudio != d["huella_estudio"]:
        raise HTTPException(409, "El estudio no coincide con el abierto en pantalla.")
    item = next((i for i in d["items"] if i["id"] == item_id), None)
    if item is None:
        raise HTTPException(404, "La fila no pertenece al estudio")
    permitidas = servicio.conclusivas(d) | {servicio.indeterminada(d)}
    if d.get("version", 1) == 1 and d["tipo"] == "DETECTOR":
        permitidas |= {"ERROR_DOCUMENTAL"}
    if payload.etiqueta not in permitidas:
        raise HTTPException(422, "La etiqueta no corresponde al tipo de estudio.")
    if d.get("version", 1) >= 2 and payload.etiqueta == "ANOMALO" and payload.criterio is None:
        raise HTTPException(
            422,
            "Identifica la inconsistencia documental verificada: cantidad, fecha, operación o área.",
        )
    if not servicio.foto_vigente(item, {}) and payload.etiqueta != servicio.indeterminada(d):
        raise HTTPException(
            409,
            "La fotografía falta o cambió respecto al corte; no se puede registrar una conclusión.",
        )
    anterior = servicio.ultimas(db, estudio_id).get(item_id)
    if payload.revision_esperada != (anterior.id if anterior else 0):
        raise HTTPException(409, "La fila ya fue revisada; actualiza antes de guardar.")
    if payload.segunda_revision and (
        d.get("version", 1) < 2
        or anterior is None
        or anterior.detalle["etiqueta"] != servicio.indeterminada(d)
    ):
        raise HTTPException(
            409, "La segunda revisión requiere una decisión indeterminada previa de esta fila."
        )
    evento = registrar_evento_auditoria(
        db,
        usuario_id=usuario.id,
        accion=servicio.ETIQUETAR,
        recurso=servicio.RECURSO,
        recurso_id=estudio_id,
        resultado="exito",
        ip_origen=request.client.host if request.client else None,
        detalle={**payload.model_dump(), "item_id": item_id, "foto_sha256": item["foto_sha256"]},
    )
    return servicio.revision_publica(evento)
