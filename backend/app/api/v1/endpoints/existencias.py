from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.crud.auditoria import registrar_evento_auditoria
from app.db.session import get_db
from app.models.activos import Activo, Existencia
from app.models.area import Area
from app.models.usuario import Usuario
from app.schemas.existencia import ExistenciaCreate, ExistenciaOut, ExistenciaUpdate

router = APIRouter(prefix="/existencias", tags=["Existencias"])


@router.get("", response_model=list[ExistenciaOut])
def listar_existencias(
    activo_id: int | None = Query(default=None),
    area_id: int | None = Query(default=None),
    estado: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    _current_user: Usuario = Depends(get_current_user),
):
    """Lista existencias con filtros opcionales y paginación. Accesible por cualquier usuario autenticado."""
    query = db.query(Existencia)
    if activo_id is not None:
        query = query.filter(Existencia.activo_id == activo_id)
    if area_id is not None:
        query = query.filter(Existencia.area_id == area_id)
    if estado is not None:
        query = query.filter(Existencia.estado == estado)

    return query.order_by(Existencia.id.asc()).offset(skip).limit(limit).all()


@router.get("/{id}", response_model=ExistenciaOut)
def obtener_existencia(
    id: int,
    db: Session = Depends(get_db),
    _current_user: Usuario = Depends(get_current_user),
):
    """Obtiene el detalle de una existencia por ID. Accesible por cualquier usuario autenticado."""
    existencia = db.query(Existencia).filter(Existencia.id == id).first()
    if not existencia:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Existencia no encontrada",
        )
    return existencia


@router.post("", response_model=ExistenciaOut, status_code=status.HTTP_201_CREATED)
def crear_existencia(
    request: Request,
    payload: ExistenciaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles("Administrador", "Operador")),
):
    """Crea un registro de existencias de un activo en un área. Administrador y Operador."""
    activo = db.query(Activo).filter(Activo.id == payload.activo_id).first()
    if not activo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El activo especificado no existe",
        )

    area = db.query(Area).filter(Area.id == payload.area_id).first()
    if not area:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El área especificada no existe",
        )

    existente = (
        db.query(Existencia)
        .filter(Existencia.activo_id == payload.activo_id, Existencia.area_id == payload.area_id)
        .first()
    )
    if existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un registro de existencia para este activo en esta área",
        )

    nueva_existencia = Existencia(
        activo_id=payload.activo_id,
        area_id=payload.area_id,
        cantidad=payload.cantidad,
        stock_minimo=payload.stock_minimo,
        stock_maximo=payload.stock_maximo,
        estado="activo",
    )
    db.add(nueva_existencia)
    db.commit()
    db.refresh(nueva_existencia)

    ip = request.client.host if request.client else None
    registrar_evento_auditoria(
        db,
        usuario_id=current_user.id,
        accion="crear_existencia",
        recurso="existencia",
        recurso_id=nueva_existencia.id,
        resultado="exito",
        ip_origen=ip,
        detalle={
            "activo_id": nueva_existencia.activo_id,
            "area_id": nueva_existencia.area_id,
            "cantidad": float(nueva_existencia.cantidad),
        },
    )

    return nueva_existencia


@router.put("/{id}", response_model=ExistenciaOut)
def actualizar_existencia(
    id: int,
    request: Request,
    payload: ExistenciaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles("Administrador", "Operador")),
):
    """Actualiza cantidad o umbrales de stock de una existencia. Administrador y Operador."""
    existencia = db.query(Existencia).filter(Existencia.id == id).first()
    if not existencia:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Existencia no encontrada",
        )

    if payload.cantidad is not None:
        existencia.cantidad = payload.cantidad
    if "stock_minimo" in payload.model_fields_set:
        existencia.stock_minimo = payload.stock_minimo
    if "stock_maximo" in payload.model_fields_set:
        existencia.stock_maximo = payload.stock_maximo

    if (
        existencia.stock_minimo is not None
        and existencia.stock_maximo is not None
        and existencia.stock_maximo < existencia.stock_minimo
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El stock máximo debe ser mayor o igual al stock mínimo",
        )

    db.commit()
    db.refresh(existencia)

    ip = request.client.host if request.client else None
    registrar_evento_auditoria(
        db,
        usuario_id=current_user.id,
        accion="editar_existencia",
        recurso="existencia",
        recurso_id=existencia.id,
        resultado="exito",
        ip_origen=ip,
        detalle={
            "activo_id": existencia.activo_id,
            "area_id": existencia.area_id,
            "cantidad": float(existencia.cantidad),
        },
    )

    return existencia


@router.patch("/{id}/desactivar", response_model=ExistenciaOut)
def desactivar_existencia(
    id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles("Administrador", "Operador")),
):
    """Desactiva una existencia (baja lógica). Administrador y Operador."""
    existencia = db.query(Existencia).filter(Existencia.id == id).first()
    if not existencia:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Existencia no encontrada",
        )

    existencia.estado = "baja"
    db.commit()
    db.refresh(existencia)

    ip = request.client.host if request.client else None
    registrar_evento_auditoria(
        db,
        usuario_id=current_user.id,
        accion="desactivar_existencia",
        recurso="existencia",
        recurso_id=existencia.id,
        resultado="exito",
        ip_origen=ip,
        detalle={
            "activo_id": existencia.activo_id,
            "area_id": existencia.area_id,
        },
    )

    return existencia


@router.patch("/{id}/reactivar", response_model=ExistenciaOut)
def reactivar_existencia(
    id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles("Administrador", "Operador")),
):
    """Reactiva una existencia en estado baja. Administrador y Operador."""
    existencia = db.query(Existencia).filter(Existencia.id == id).first()
    if not existencia:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Existencia no encontrada",
        )

    existencia.estado = "activo"
    db.commit()
    db.refresh(existencia)

    ip = request.client.host if request.client else None
    registrar_evento_auditoria(
        db,
        usuario_id=current_user.id,
        accion="reactivar_existencia",
        recurso="existencia",
        recurso_id=existencia.id,
        resultado="exito",
        ip_origen=ip,
        detalle={
            "activo_id": existencia.activo_id,
            "area_id": existencia.area_id,
        },
    )

    return existencia
