from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.crud.auditoria import registrar_evento_auditoria
from app.db.session import get_db
from app.models.activos import CategoriaActivo
from app.models.usuario import Usuario
from app.schemas.categoria_activo import (
    CategoriaActivoCreate,
    CategoriaActivoOut,
    CategoriaActivoUpdate,
)

router = APIRouter(prefix="/categorias", tags=["Categorías de Activos"])


@router.get("", response_model=list[CategoriaActivoOut])
def listar_categorias(
    estado: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    _current_user: Usuario = Depends(get_current_user),
):
    """Lista las categorías de activos. Accesible por cualquier usuario autenticado."""
    query = db.query(CategoriaActivo)
    if estado is not None:
        query = query.filter(CategoriaActivo.estado == estado)
    return query.order_by(CategoriaActivo.id.asc()).offset(skip).limit(limit).all()


@router.get("/{id}", response_model=CategoriaActivoOut)
def obtener_categoria(
    id: int,
    db: Session = Depends(get_db),
    _current_user: Usuario = Depends(get_current_user),
):
    """Obtiene el detalle de una categoría. Accesible por cualquier usuario autenticado."""
    categoria = db.query(CategoriaActivo).filter(CategoriaActivo.id == id).first()
    if not categoria:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoría no encontrada",
        )
    return categoria


@router.post("", response_model=CategoriaActivoOut, status_code=status.HTTP_201_CREATED)
def crear_categoria(
    request: Request,
    payload: CategoriaActivoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles("Administrador")),
):
    """Crea una nueva categoría de activos. Solo Administrador."""
    existente_nombre = db.query(CategoriaActivo).filter(CategoriaActivo.nombre == payload.nombre).first()
    if existente_nombre:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una categoría con ese nombre",
        )

    if payload.codigo:
        existente_codigo = db.query(CategoriaActivo).filter(CategoriaActivo.codigo == payload.codigo).first()
        if existente_codigo:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe una categoría con ese código",
            )

    nueva_categoria = CategoriaActivo(
        nombre=payload.nombre,
        codigo=payload.codigo,
        descripcion=payload.descripcion,
        estado="activo",
    )
    db.add(nueva_categoria)
    db.commit()
    db.refresh(nueva_categoria)

    ip = request.client.host if request.client else None
    registrar_evento_auditoria(
        db,
        usuario_id=current_user.id,
        accion="crear_categoria_activo",
        recurso="categoria_activo",
        recurso_id=nueva_categoria.id,
        resultado="exito",
        ip_origen=ip,
        detalle={"nombre": nueva_categoria.nombre, "codigo": nueva_categoria.codigo},
    )

    return nueva_categoria


@router.put("/{id}", response_model=CategoriaActivoOut)
def actualizar_categoria(
    id: int,
    request: Request,
    payload: CategoriaActivoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles("Administrador")),
):
    """Actualiza datos de una categoría. Solo Administrador."""
    categoria = db.query(CategoriaActivo).filter(CategoriaActivo.id == id).first()
    if not categoria:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoría no encontrada",
        )

    if payload.nombre is not None and payload.nombre != categoria.nombre:
        existente_nombre = (
            db.query(CategoriaActivo)
            .filter(CategoriaActivo.nombre == payload.nombre, CategoriaActivo.id != id)
            .first()
        )
        if existente_nombre:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe una categoría con ese nombre",
            )
        categoria.nombre = payload.nombre

    if payload.codigo is not None and payload.codigo != categoria.codigo:
        existente_codigo = (
            db.query(CategoriaActivo)
            .filter(CategoriaActivo.codigo == payload.codigo, CategoriaActivo.id != id)
            .first()
        )
        if existente_codigo:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe una categoría con ese código",
            )
        categoria.codigo = payload.codigo

    if payload.descripcion is not None:
        categoria.descripcion = payload.descripcion

    db.commit()
    db.refresh(categoria)

    ip = request.client.host if request.client else None
    registrar_evento_auditoria(
        db,
        usuario_id=current_user.id,
        accion="editar_categoria_activo",
        recurso="categoria_activo",
        recurso_id=categoria.id,
        resultado="exito",
        ip_origen=ip,
        detalle={"nombre": categoria.nombre, "codigo": categoria.codigo},
    )

    return categoria


@router.patch("/{id}/desactivar", response_model=CategoriaActivoOut)
def desactivar_categoria(
    id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles("Administrador")),
):
    """Desactiva una categoría (baja lógica). Solo Administrador."""
    categoria = db.query(CategoriaActivo).filter(CategoriaActivo.id == id).first()
    if not categoria:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoría no encontrada",
        )

    categoria.estado = "baja"
    db.commit()
    db.refresh(categoria)

    ip = request.client.host if request.client else None
    registrar_evento_auditoria(
        db,
        usuario_id=current_user.id,
        accion="desactivar_categoria_activo",
        recurso="categoria_activo",
        recurso_id=categoria.id,
        resultado="exito",
        ip_origen=ip,
        detalle={"nombre": categoria.nombre},
    )

    return categoria


@router.patch("/{id}/reactivar", response_model=CategoriaActivoOut)
def reactivar_categoria(
    id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles("Administrador")),
):
    """Reactiva una categoría en estado baja. Solo Administrador."""
    categoria = db.query(CategoriaActivo).filter(CategoriaActivo.id == id).first()
    if not categoria:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoría no encontrada",
        )

    categoria.estado = "activo"
    db.commit()
    db.refresh(categoria)

    ip = request.client.host if request.client else None
    registrar_evento_auditoria(
        db,
        usuario_id=current_user.id,
        accion="reactivar_categoria_activo",
        recurso="categoria_activo",
        recurso_id=categoria.id,
        resultado="exito",
        ip_origen=ip,
        detalle={"nombre": categoria.nombre},
    )

    return categoria
