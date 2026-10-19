"""Bandeja de revisión humana. Ninguna decisión cambia cantidades."""
from datetime import UTC, date, datetime, time, timedelta
from typing import Literal
from uuid import UUID
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import String, case, cast, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.api.deps import require_roles
from app.db.session import get_db
from app.models.activos import Activo
from app.models.area import Area
from app.models.auditoria import AuditoriaSistema
from app.models.control_alertas import CasoControl, RevisionControl
from app.models.inventario import AperturaInventario
from app.models.rol import Rol
from app.models.usuario import Usuario
from app.services.control_alertas import contexto_actual, huella
from app.services.periodos import limites_gestion

router = APIRouter(prefix="/control-alertas", tags=["Seguimiento de alertas operativas"])
lector = require_roles("Administrador", "Auditor", "Operador")
revisor = require_roles("Administrador", "Auditor")
Estado = Literal["PENDIENTE", "EN_REVISION", "SEGUIMIENTO", "JUSTIFICADO", "CERRADO"]
Prioridad = Literal["ALTA", "MEDIA", "BAJA"]
Conclusion = Literal["LEGITIMO", "REQUIERE_CORRECCION", "NO_CONCLUYENTE", "CORREGIDO"]

class Decision(BaseModel):
    solicitud_id: UUID
    revision_esperada: int = Field(ge=0)
    huella_contexto: str = Field(pattern=r"^[a-f0-9]{64}$")
    estado: Estado
    prioridad: Prioridad
    asignado_id: int = Field(gt=0)
    conclusion: Conclusion = "NO_CONCLUYENTE"
    motivo: str = Field(min_length=10, max_length=2000)
    documento: str | None = Field(default=None, max_length=200)
    correccion_movimiento_id: int | None = Field(default=None, gt=0)

    @field_validator("motivo", "documento", mode="before")
    @classmethod
    def limpiar(cls, valor):
        return valor.strip() if isinstance(valor, str) else valor

def obtener(db, id):
    c = db.get(CasoControl, id)
    if c is None:
        raise HTTPException(404, "Caso no encontrado")
    return c

def resumen(c, articulo=None):
    return {k: getattr(c, k) for k in ("id", "articulo_id", "estado", "prioridad",
        "asignado_id", "asignado_nombre", "revision_numero", "creado_en", "actualizado_en", "conclusion")} | {
        "articulo": articulo.nombre if articulo else None, "codigo": articulo.codigo if articulo else None,
        "operacion": c.snapshot}

def historial(db, caso_id, pagina=1, limite=50):
    q = db.query(RevisionControl).filter_by(caso_id=caso_id)
    return {"total": q.count(), "filas": [{k: getattr(r, k) for k in ("id", "usuario_id",
        "usuario_nombre", "creado_en", "anterior", "nuevo", "motivo", "documento",
        "correccion_movimiento_id")} for r in q.order_by(RevisionControl.id.desc()).offset(
            (pagina - 1) * limite).limit(limite)]}

def detalle(db, c):
    actual = contexto_actual(db, c)
    ids = {actual.get(k) for k in ("encargado_id", "registrador_id") if actual.get(k)}
    areas = {actual.get(k) for k in ("area_origen_id", "area_destino_id") if actual.get(k)}
    return resumen(c, db.get(Activo, c.articulo_id)) | {"actual": actual,
        "huella_contexto": huella(actual), "historial": historial(db, c.id),
        "personas": {u.id: u.nombre for u in db.query(Usuario).filter(Usuario.id.in_(ids))},
        "areas": {a.id: a.nombre for a in db.query(Area).filter(Area.id.in_(areas))}}

@router.get("/revisores")
def revisores(db: Session = Depends(get_db), _=Depends(lector)):
    return [{"id": u.id, "nombre": u.nombre, "rol": u.rol.nombre} for u in db.query(Usuario).join(Rol).filter(
        Usuario.estado == "activo", Rol.nombre.in_(("Administrador", "Auditor"))
    ).order_by(Usuario.nombre, Usuario.id)]

@router.get("")
def listar(estado: Literal["ABIERTOS", "TODOS", "PENDIENTE", "EN_REVISION", "SEGUIMIENTO", "JUSTIFICADO", "CERRADO"] = "ABIERTOS",
    prioridad: Prioridad | None = None, articulo_id: int | None = Query(None, gt=0),
    asignado_id: int | None = Query(None, gt=0), sin_asignar: bool = False,
    codigo: str | None = Query(None, pattern=r"^[A-Z_]{3,60}$"),
    gestion: int | None = Query(None, ge=1900, le=9998),
    desde: date | None = None, hasta: date | None = None,
    pagina: int = Query(1, ge=1), limite: int = Query(30, ge=1, le=100),
    db: Session = Depends(get_db), _=Depends(lector)):
    if desde and hasta and desde > hasta:
        raise HTTPException(422, "El inicio no puede ser posterior al fin")
    if sin_asignar and asignado_id:
        raise HTTPException(422, "Selecciona un revisor o sin asignar")
    q = db.query(CasoControl)
    if estado == "ABIERTOS":
        q = q.filter(CasoControl.estado.in_(("PENDIENTE", "EN_REVISION", "SEGUIMIENTO")))
    elif estado != "TODOS":
        q = q.filter(CasoControl.estado == estado)
    if prioridad:
        q = q.filter(CasoControl.prioridad == prioridad)
    if articulo_id:
        q = q.filter(CasoControl.articulo_id == articulo_id)
    if asignado_id:
        q = q.filter(CasoControl.asignado_id == asignado_id)
    if sin_asignar:
        q = q.filter(CasoControl.asignado_id.is_(None))
    if codigo:
        codigo_json = '%"' + codigo.replace("_", "\\_") + '"%'
        q = q.filter(cast(CasoControl.codigos, String).like(codigo_json, escape="\\"))
    zona = ZoneInfo("America/La_Paz")
    if gestion is not None:
        inicio, fin = limites_gestion(gestion)
        q = q.filter(CasoControl.creado_en >= inicio, CasoControl.creado_en < fin)
    if desde:
        q = q.filter(CasoControl.creado_en >= datetime.combine(desde, time.min, tzinfo=zona).astimezone(UTC))
    if hasta:
        q = q.filter(CasoControl.creado_en < datetime.combine(hasta + timedelta(days=1), time.min, tzinfo=zona).astimezone(UTC))
    conteos = dict(q.with_entities(CasoControl.estado, func.count()).group_by(CasoControl.estado).all())
    filas = q.order_by(case((CasoControl.prioridad == "ALTA", 0), (CasoControl.prioridad == "MEDIA", 1), else_=2),
        CasoControl.creado_en.desc(), CasoControl.id.desc()).offset((pagina-1)*limite).limit(limite).all()
    articulos = {a.id: a for a in db.query(Activo).filter(Activo.id.in_({c.articulo_id for c in filas}))}
    return {"total": sum(conteos.values()), "conteos": conteos,
        "filas": [resumen(c, articulos[c.articulo_id]) for c in filas]}

@router.get("/{caso_id}/revisiones")
def revisiones(caso_id: int, pagina: int = Query(1, ge=1), limite: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db), _=Depends(lector)):
    obtener(db, caso_id)
    return historial(db, caso_id, pagina, limite)

@router.get("/{caso_id}")
def consultar(caso_id: int, db: Session = Depends(get_db), _=Depends(lector)):
    return detalle(db, obtener(db, caso_id))

@router.post("/{caso_id}/revision")
def revisar(caso_id: int, payload: Decision, request: Request, db: Session = Depends(get_db),
            usuario=Depends(revisor)):
    c = obtener(db, caso_id)
    identidad = huella(payload.model_dump(mode="json") | {"caso_id": caso_id, "usuario_id": usuario.id})
    def repetida():
        previa = db.query(RevisionControl).filter_by(solicitud_id=str(payload.solicitud_id)).first()
        if previa:
            if previa.solicitud_huella != identidad:
                raise HTTPException(409, "La clave de revisión ya se utilizó con otros datos")
            return detalle(db, obtener(db, caso_id)) | {"reintento": True}
        return None
    resultado = repetida()
    if resultado:
        return resultado
    # Mismo bloqueo que las operaciones: su evidencia no puede cambiar entre
    # la comprobación del contexto y la persistencia de esta decisión.
    db.query(AperturaInventario).filter_by(articulo_id=c.articulo_id).with_for_update().first()
    db.refresh(c)
    resultado = repetida()
    if resultado:
        db.rollback()
        return resultado
    if payload.revision_esperada != c.revision_numero:
        raise HTTPException(409, "Otra persona revisó el caso. Actualiza el detalle antes de decidir")
    actual = contexto_actual(db, c)
    if payload.huella_contexto != huella(actual):
        raise HTTPException(409, "Cambió la operación vinculada. Actualiza y revisa su evidencia")
    asignado = db.query(Usuario).join(Rol).filter(Usuario.id == payload.asignado_id,
        Usuario.estado == "activo", Rol.nombre.in_(("Administrador", "Auditor"))).first()
    if asignado is None:
        raise HTTPException(422, "Asigna el caso a un administrador o auditor activo")
    if len(payload.motivo.strip()) < 10:
        raise HTTPException(422, "Escribe un motivo concreto de al menos 10 caracteres")
    destinos = {"PENDIENTE": {"EN_REVISION"}, "EN_REVISION": {"EN_REVISION", "SEGUIMIENTO", "JUSTIFICADO", "CERRADO"},
        "SEGUIMIENTO": {"EN_REVISION", "SEGUIMIENTO", "JUSTIFICADO", "CERRADO"},
        "JUSTIFICADO": {"EN_REVISION"}, "CERRADO": {"EN_REVISION"}}
    if payload.estado not in destinos[c.estado]:
        raise HTTPException(422, "Abre o reabre el caso en revisión antes de resolverlo")
    resuelto = payload.estado in ("JUSTIFICADO", "CERRADO")
    if payload.estado == "JUSTIFICADO" and payload.conclusion != "LEGITIMO":
        raise HTTPException(422, "Justificado requiere la conclusión Legítimo")
    if resuelto and payload.conclusion not in ("LEGITIMO", "CORREGIDO"):
        raise HTTPException(422, "Un caso no concluyente o con corrección pendiente debe permanecer abierto")
    if resuelto and len((payload.documento or "").strip()) < 3:
        raise HTTPException(422, "Resolver el caso requiere una referencia documental")
    if payload.conclusion == "CORREGIDO":
        if (not c.movimiento_id or not payload.correccion_movimiento_id or
            actual.get("ultima_rectificacion_id") != payload.correccion_movimiento_id):
            raise HTTPException(422, "Vincula la última rectificación del movimiento de este caso")
    elif payload.correccion_movimiento_id:
        raise HTTPException(422, "La rectificación vinculada requiere la conclusión Corregido")
    anterior = {k: getattr(c, k) for k in ("estado", "prioridad", "asignado_id", "asignado_nombre", "conclusion", "revision_numero")}
    ahora = datetime.now(UTC)
    nuevo = dict(estado=payload.estado, prioridad=payload.prioridad, asignado_id=asignado.id,
        asignado_nombre=asignado.nombre, conclusion=payload.conclusion, revision_numero=payload.revision_esperada + 1)
    cambiado = db.query(CasoControl).filter(CasoControl.id == caso_id,
        CasoControl.revision_numero == payload.revision_esperada).update(
            nuevo | {"actualizado_en": ahora}, synchronize_session=False)
    if not cambiado:
        db.rollback()
        raise HTTPException(409, "Otra persona revisó el caso. Actualiza el detalle")
    r = RevisionControl(caso_id=caso_id, solicitud_id=str(payload.solicitud_id), solicitud_huella=identidad,
        usuario_id=usuario.id, usuario_nombre=usuario.nombre, creado_en=ahora, anterior=anterior, nuevo=nuevo,
        motivo=payload.motivo, documento=payload.documento, correccion_movimiento_id=payload.correccion_movimiento_id,
        huella_contexto=payload.huella_contexto)
    db.add(r)
    db.add(AuditoriaSistema(usuario_id=usuario.id, accion="revisar_alerta_operativa", recurso="caso_control",
        recurso_id=caso_id, resultado="exito", fecha_hora=ahora, ip_origen=request.client.host if request.client else None,
        detalle={"anterior": anterior, "nuevo": nuevo, "motivo": payload.motivo, "documento": payload.documento,
                 "correccion_movimiento_id": payload.correccion_movimiento_id}))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        resultado = repetida()
        if resultado:
            return resultado
        raise
    db.refresh(c)
    return detalle(db, c)
