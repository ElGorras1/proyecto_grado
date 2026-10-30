"""Administración separada de ubicaciones, catálogo documental y equivalencias."""
import hashlib
import json
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.api.v1.endpoints.usuarios import bloquear_administracion
from app.db.session import get_db
from app.models.activos import Existencia
from app.models.area import Area
from app.models.catalogo_areas import CatalogoArea, SinonimoArea
from app.models.inventario import CustodiaExterna
from app.models.kardex import MovimientoKardex
from app.models.usuario import Usuario
from app.models.auditoria import AuditoriaSistema
from app.services.inventario import auditar
from app.db.session import Base

router = APIRouter(prefix="/administracion/areas", tags=["Áreas y catálogos"])
lector = require_roles("Administrador", "Auditor")
editor = require_roles("Administrador")


@router.get("/historial")
def historial(
    recurso: Literal["area", "catalogo_areas", "sinonimos_area", "usuario"],
    registro_id: int = Query(gt=0), limite: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db), _=Depends(lector),
):
    registros = db.query(AuditoriaSistema, Usuario.nombre).outerjoin(
        Usuario, Usuario.id == AuditoriaSistema.usuario_id).filter(
        AuditoriaSistema.accion == "administrar_areas_catalogos",
        AuditoriaSistema.recurso == recurso, AuditoriaSistema.recurso_id == registro_id,
    ).order_by(AuditoriaSistema.id.desc()).limit(limite).all()
    return [{"id": a.id, "fecha": a.fecha_hora, "usuario": nombre,
             "detalle": a.detalle} for a, nombre in registros]


class Decision(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    motivo: str = Field(min_length=10, max_length=2000)
    version: str | None = Field(default=None, pattern="^[a-f0-9]{64}$")


class AreaDatos(Decision):
    nombre: str = Field(min_length=1, max_length=120)
    codigo: str | None = Field(default=None, max_length=30)
    descripcion: str | None = Field(default=None, max_length=255)
    estado: Literal["activo", "baja"] = "activo"

    @field_validator("codigo", "descripcion")
    @classmethod
    def vacio_a_nulo(cls, valor):
        return valor or None


class CatalogoDatos(Decision):
    nombre_oficial: str = Field(min_length=1, max_length=100)
    abreviatura: str | None = Field(default=None, max_length=30)
    descripcion: str | None = Field(default=None, max_length=2000)
    tipo: Literal["departamento", "operacion"] = "departamento"
    activa: bool = True

    @field_validator("abreviatura", "descripcion")
    @classmethod
    def vacio_a_nulo(cls, valor):
        return valor or None


class AliasDatos(Decision):
    texto_sucio: str = Field(min_length=1, max_length=200)
    area_oficial_id: int = Field(gt=0)
    confirmado: bool = False
    activa: bool = True
    evidencia_revisada: bool = False


class AdscripcionDatos(Decision):
    area_id: int | None = Field(default=None, gt=0)


CAMPOS = {
    Area: ("nombre", "codigo", "descripcion", "estado"),
    CatalogoArea: ("nombre_oficial", "abreviatura", "descripcion", "tipo", "activa"),
    SinonimoArea: ("texto_sucio", "area_oficial_id", "confirmado", "activa"),
    Usuario: ("nombre", "area_id", "estado"),
}


def snapshot(row):
    datos = {"id": row.id, **{c: getattr(row, c) for c in CAMPOS[type(row)]}}
    version = hashlib.sha256(json.dumps(datos, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return {**datos, "version": version}


def fila(db, modelo, id):
    row = db.query(modelo).filter(modelo.id == id).populate_existing().with_for_update().first()
    if row is None:
        raise HTTPException(404, "Registro no encontrado")
    return row


def vigente(row, version):
    if version != snapshot(row)["version"]:
        raise HTTPException(409, "El registro cambió. Actualiza la lista y vuelve a abrirlo para revisar los valores.")


def guardar(db, usuario, request, row, previo, motivo):
    try:
        db.flush()
        nuevo = snapshot(row)
        auditar(db, usuario, request, "administrar_areas_catalogos", row.__tablename__, row.id,
                {"previo": previo, "nuevo": nuevo, "motivo": motivo})
        db.commit()
        return nuevo
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "El nombre, código o alias ya existe; revisa también los registros de baja.")


def clave(columna, valor):
    return func.upper(func.trim(columna)) == valor.strip().upper()


def validar_unicos(db, modelo, valores, id=None):
    for campo, valor in valores.items():
        if valor and db.query(modelo.id).filter(clave(getattr(modelo, campo), valor),
                                               modelo.id != id if id else True).first():
            raise HTTPException(409, "El nombre, código o alias ya existe, incluso si está de baja.")


def validar_clave_documental(db, textos, destino_id):
    """Un alias no puede ocultar el nombre o sigla de otra unidad."""
    for texto in filter(None, textos):
        if db.query(CatalogoArea.id).filter(
            or_(clave(CatalogoArea.nombre_oficial, texto), clave(CatalogoArea.abreviatura, texto)),
            CatalogoArea.id != destino_id if destino_id else True).first():
            raise HTTPException(409, "La lectura coincide con el nombre o sigla de otra entrada del catálogo.")
        if db.query(SinonimoArea.id).filter(clave(SinonimoArea.texto_sucio, texto),
                                           SinonimoArea.area_oficial_id != destino_id if destino_id else True).first():
            raise HTTPException(409, "La lectura está reservada como alias de otra entrada.")


def dependencias_area(db, id):
    return {
        "stock": float(db.query(func.coalesce(func.sum(Existencia.cantidad), 0)).filter(Existencia.area_id == id).scalar()),
        "custodias_abiertas": db.query(CustodiaExterna.id).filter(CustodiaExterna.area_origen_id == id, CustodiaExterna.cantidad_fuera > 0).count(),
        "usuarios_activos": db.query(Usuario.id).filter(Usuario.area_id == id, Usuario.estado == "activo").count(),
    }


def identidad_area_usada(db, id):
    for tabla in Base.metadata.tables.values():
        for columna in tabla.columns:
            if any(fk.target_fullname == "area.id" for fk in columna.foreign_keys):
                if db.query(columna).filter(columna == id).first():
                    return True
    return False


@router.get("")
def listar_areas(db: Session = Depends(get_db), _=Depends(lector)):
    return [{**snapshot(a), "dependencias": dependencias_area(db, a.id)}
            for a in db.query(Area).order_by(Area.nombre, Area.id)]


@router.post("", status_code=201)
def crear_area(payload: AreaDatos, request: Request, db: Session = Depends(get_db), usuario=Depends(editor)):
    bloquear_administracion(db, usuario)
    validar_unicos(db, Area, {"nombre": payload.nombre, "codigo": payload.codigo})
    row = Area(**payload.model_dump(exclude={"motivo", "version"}))
    db.add(row)
    return guardar(db, usuario, request, row, None, payload.motivo)


@router.put("/{id}")
def editar_area(id: int, payload: AreaDatos, request: Request, db: Session = Depends(get_db), usuario=Depends(editor)):
    bloquear_administracion(db, usuario)
    row = fila(db, Area, id)
    vigente(row, payload.version)
    previo = snapshot(row)
    dependencias = dependencias_area(db, id)
    if row.nombre != payload.nombre and identidad_area_usada(db, id):
        raise HTTPException(409, "El nombre identifica un área ya utilizada. Conserva su identidad; puedes editar código y descripción.")
    if payload.estado == "baja" and any(dependencias.values()):
        raise HTTPException(409, "No se puede dar de baja: retira el stock, resuelve custodias y reasigna usuarios activos.")
    validar_unicos(db, Area, {"nombre": payload.nombre, "codigo": payload.codigo}, id)
    for campo in CAMPOS[Area]:
        setattr(row, campo, getattr(payload, campo))
    return guardar(db, usuario, request, row, previo, payload.motivo)


@router.get("/catalogo/historico")
def listar_catalogo(db: Session = Depends(get_db), _=Depends(lector)):
    return [snapshot(a) for a in db.query(CatalogoArea).order_by(CatalogoArea.nombre_oficial)]


@router.post("/catalogo/historico", status_code=201)
def crear_catalogo(payload: CatalogoDatos, request: Request, db: Session = Depends(get_db), usuario=Depends(editor)):
    bloquear_administracion(db, usuario)
    validar_clave_documental(db, [payload.nombre_oficial, payload.abreviatura], None)
    row = CatalogoArea(**payload.model_dump(exclude={"motivo", "version"}))
    db.add(row)
    return guardar(db, usuario, request, row, None, payload.motivo)


@router.put("/catalogo/historico/{id}")
def editar_catalogo(id: int, payload: CatalogoDatos, request: Request, db: Session = Depends(get_db), usuario=Depends(editor)):
    bloquear_administracion(db, usuario)
    row = fila(db, CatalogoArea, id)
    vigente(row, payload.version)
    previo = snapshot(row)
    if row.nombre_oficial != payload.nombre_oficial or row.tipo != payload.tipo:
        usado = db.query(SinonimoArea.id).filter(SinonimoArea.area_oficial_id == id).first()
        # El nodo se conserva como texto en el histórico: no se renombra masivamente.
        usado = usado or db.query(MovimientoKardex.id).filter(or_(
            MovimientoKardex.nodo_grafo == "Área: " + row.nombre_oficial,
            clave(MovimientoKardex.area, row.nombre_oficial),
            clave(MovimientoKardex.area, row.abreviatura) if row.abreviatura else False,
            MovimientoKardex.nodo_grafo == row.nombre_oficial,
            MovimientoKardex.nodo_grafo == "Salida: " + row.nombre_oficial,
            MovimientoKardex.nodo_grafo == "Entrada: " + row.nombre_oficial,
        )).first()
        if usado:
            raise HTTPException(409, "La identidad está usada por el histórico o sus alias. Conserva su nombre/tipo y crea otra entrada si corresponde.")
    validar_clave_documental(db, [payload.nombre_oficial, payload.abreviatura], id)
    for campo in CAMPOS[CatalogoArea]:
        setattr(row, campo, getattr(payload, campo))
    return guardar(db, usuario, request, row, previo, payload.motivo)


@router.get("/catalogo/alias")
def listar_alias(db: Session = Depends(get_db), _=Depends(lector)):
    return [snapshot(a) for a in db.query(SinonimoArea).order_by(SinonimoArea.texto_sucio)]


def validar_alias(db, payload, id=None):
    if not db.get(CatalogoArea, payload.area_oficial_id):
        raise HTTPException(422, "Selecciona una entrada del catálogo documental.")
    validar_unicos(db, SinonimoArea, {"texto_sucio": payload.texto_sucio}, id)
    validar_clave_documental(db, [payload.texto_sucio], payload.area_oficial_id)
    if payload.confirmado and not payload.evidencia_revisada:
        raise HTTPException(422, "Confirmar una equivalencia requiere cotejar su evidencia.")


@router.post("/catalogo/alias", status_code=201)
def crear_alias(payload: AliasDatos, request: Request, db: Session = Depends(get_db), usuario=Depends(editor)):
    bloquear_administracion(db, usuario)
    validar_alias(db, payload)
    row = SinonimoArea(**payload.model_dump(exclude={"motivo", "version", "evidencia_revisada"}))
    db.add(row)
    return guardar(db, usuario, request, row, None, payload.motivo)


@router.put("/catalogo/alias/{id}")
def editar_alias(id: int, payload: AliasDatos, request: Request, db: Session = Depends(get_db), usuario=Depends(editor)):
    bloquear_administracion(db, usuario)
    row = fila(db, SinonimoArea, id)
    vigente(row, payload.version)
    if payload.texto_sucio != row.texto_sucio:
        raise HTTPException(409, "Conserva la lectura original del alias; crea otro y da de baja este si corresponde.")
    previo = snapshot(row)
    # Se excluye el propio alias del control de destino anterior al reasignarlo.
    validar_unicos(db, SinonimoArea, {"texto_sucio": payload.texto_sucio}, id)
    if not db.get(CatalogoArea, payload.area_oficial_id):
        raise HTTPException(422, "Selecciona una entrada del catálogo documental.")
    if db.query(CatalogoArea.id).filter(or_(clave(CatalogoArea.nombre_oficial, payload.texto_sucio),
        clave(CatalogoArea.abreviatura, payload.texto_sucio)), CatalogoArea.id != payload.area_oficial_id).first():
        raise HTTPException(409, "El alias coincide con el nombre o sigla de otra entrada.")
    if payload.confirmado and not payload.evidencia_revisada:
        raise HTTPException(422, "Confirmar una equivalencia requiere cotejar su evidencia.")
    for campo in CAMPOS[SinonimoArea]:
        setattr(row, campo, getattr(payload, campo))
    return guardar(db, usuario, request, row, previo, payload.motivo)


@router.get("/personas/adscripciones")
def listar_adscripciones(db: Session = Depends(get_db), _=Depends(lector)):
    return [snapshot(u) for u in db.query(Usuario).order_by(Usuario.nombre, Usuario.id)]


@router.put("/personas/adscripciones/{id}")
def editar_adscripcion(id: int, payload: AdscripcionDatos, request: Request, db: Session = Depends(get_db), usuario=Depends(editor)):
    bloquear_administracion(db, usuario)
    row = fila(db, Usuario, id)
    vigente(row, payload.version)
    previo = snapshot(row)
    if payload.area_id is not None:
        area = fila(db, Area, payload.area_id)
        if area.estado != "activo":
            raise HTTPException(422, "Selecciona un área operativa activa.")
    row.area_id = payload.area_id
    return guardar(db, usuario, request, row, previo, payload.motivo)
