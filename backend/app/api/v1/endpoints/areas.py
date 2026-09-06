from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.crud.auditoria import registrar_evento_auditoria
from app.db.session import get_db
from app.models.area import Area
from app.models.usuario import Usuario
from app.schemas.area import AreaCreate, AreaOut, AreaUpdate

router = APIRouter(prefix="/areas", tags=["Áreas"])


@router.get("", response_model=list[AreaOut])
def listar_areas(
    estado: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _current_user: Usuario = Depends(get_current_user),
):
    """Lista las áreas operativas. Accesible por cualquier usuario autenticado."""
    query = db.query(Area)
    if estado is not None:
        query = query.filter(Area.estado == estado)
    return query.order_by(Area.id.asc()).all()


@router.get("/{id}", response_model=AreaOut)
def obtener_area(
    id: int,
    db: Session = Depends(get_db),
    _current_user: Usuario = Depends(get_current_user),
):
    """Obtiene el detalle de un área. Accesible por cualquier usuario autenticado."""
    area = db.query(Area).filter(Area.id == id).first()
    if not area:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Área no encontrada",
        )
    return area


@router.post("", response_model=AreaOut, status_code=status.HTTP_201_CREATED)
def crear_area(
    request: Request,
    payload: AreaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles("Administrador")),
):
    """Crea una nueva área operativa. Solo Administrador."""
    existente_nombre = db.query(Area).filter(Area.nombre == payload.nombre).first()
    if existente_nombre:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un área con ese nombre",
        )

    if payload.codigo:
        existente_codigo = db.query(Area).filter(Area.codigo == payload.codigo).first()
        if existente_codigo:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe un área con ese código",
            )

    nueva_area = Area(
        nombre=payload.nombre,
        codigo=payload.codigo,
        descripcion=payload.descripcion,
        estado="activo",
    )
    db.add(nueva_area)
    db.commit()
    db.refresh(nueva_area)

    ip = request.client.host if request.client else None
    registrar_evento_auditoria(
        db,
        usuario_id=current_user.id,
        accion="crear_area",
        recurso="area",
        recurso_id=nueva_area.id,
        resultado="exito",
        ip_origen=ip,
        detalle={"nombre": nueva_area.nombre, "codigo": nueva_area.codigo},
    )

    return nueva_area


@router.put("/{id}", response_model=AreaOut)
def actualizar_area(
    id: int,
    request: Request,
    payload: AreaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles("Administrador")),
):
    """Actualiza datos de un área. Solo Administrador."""
    area = db.query(Area).filter(Area.id == id).first()
    if not area:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Área no encontrada",
        )

    if payload.nombre is not None and payload.nombre != area.nombre:
        existente_nombre = db.query(Area).filter(Area.nombre == payload.nombre, Area.id != id).first()
        if existente_nombre:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe un área con ese nombre",
            )
        area.nombre = payload.nombre

    if payload.codigo is not None and payload.codigo != area.codigo:
        existente_codigo = db.query(Area).filter(Area.codigo == payload.codigo, Area.id != id).first()
        if existente_codigo:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe un área con ese código",
            )
        area.codigo = payload.codigo

    if payload.descripcion is not None:
        area.descripcion = payload.descripcion

    db.commit()
    db.refresh(area)

    ip = request.client.host if request.client else None
    registrar_evento_auditoria(
        db,
        usuario_id=current_user.id,
        accion="editar_area",
        recurso="area",
        recurso_id=area.id,
        resultado="exito",
        ip_origen=ip,
        detalle={"nombre": area.nombre, "codigo": area.codigo},
    )

    return area


@router.patch("/{id}/desactivar", response_model=AreaOut)
def desactivar_area(
    id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles("Administrador")),
):
    """Desactiva un área (baja lógica). Solo Administrador."""
    area = db.query(Area).filter(Area.id == id).first()
    if not area:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Área no encontrada",
        )

    area.estado = "baja"
    db.commit()
    db.refresh(area)

    ip = request.client.host if request.client else None
    registrar_evento_auditoria(
        db,
        usuario_id=current_user.id,
        accion="desactivar_area",
        recurso="area",
        recurso_id=area.id,
        resultado="exito",
        ip_origen=ip,
        detalle={"nombre": area.nombre},
    )

    return area


@router.patch("/{id}/reactivar", response_model=AreaOut)
def reactivar_area(
    id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles("Administrador")),
):
    """Reactiva un área en estado baja. Solo Administrador."""
    area = db.query(Area).filter(Area.id == id).first()
    if not area:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Área no encontrada",
        )

    area.estado = "activo"
    db.commit()
    db.refresh(area)

    ip = request.client.host if request.client else None
    registrar_evento_auditoria(
        db,
        usuario_id=current_user.id,
        accion="reactivar_area",
        recurso="area",
        recurso_id=area.id,
        resultado="exito",
        ip_origen=ip,
        detalle={"nombre": area.nombre},
    )

    return area
