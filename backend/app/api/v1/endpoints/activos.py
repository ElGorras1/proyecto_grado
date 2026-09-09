from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.crud.auditoria import registrar_evento_auditoria
from app.db.session import get_db
from app.models.activos import Activo, CategoriaActivo
from app.models.usuario import Usuario
from app.schemas.activo import ActivoCreate, ActivoOut, ActivoUpdate

router = APIRouter(prefix="/activos", tags=["Activos"])


@router.get("", response_model=list[ActivoOut])
def listar_activos(
    categoria_id: int | None = Query(default=None),
    estado: str | None = Query(default=None),
    search: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    _current_user: Usuario = Depends(get_current_user),
):
    """Lista activos con filtros opcionales y paginación. Accesible por cualquier usuario autenticado."""
    query = db.query(Activo)
    if categoria_id is not None:
        query = query.filter(Activo.categoria_id == categoria_id)
    if estado is not None:
        query = query.filter(Activo.estado == estado)
    if search:
        termino = f"%{search}%"
        query = query.filter((Activo.codigo.ilike(termino)) | (Activo.nombre.ilike(termino)))

    return query.order_by(Activo.id.asc()).offset(skip).limit(limit).all()


@router.get("/{id}", response_model=ActivoOut)
def obtener_activo(
    id: int,
    db: Session = Depends(get_db),
    _current_user: Usuario = Depends(get_current_user),
):
    """Obtiene el detalle de un activo. Accesible por cualquier usuario autenticado."""
    activo = db.query(Activo).filter(Activo.id == id).first()
    if not activo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activo no encontrado",
        )
    return activo


@router.post("", response_model=ActivoOut, status_code=status.HTTP_201_CREATED)
def crear_activo(
    request: Request,
    payload: ActivoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles("Administrador", "Operador")),
):
    """Crea un nuevo activo. Administrador y Operador."""
    categoria = db.query(CategoriaActivo).filter(CategoriaActivo.id == payload.categoria_id).first()
    if not categoria:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La categoría especificada no existe",
        )

    existente_codigo = db.query(Activo).filter(Activo.codigo == payload.codigo).first()
    if existente_codigo:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un activo con ese código",
        )

    nuevo_activo = Activo(
        categoria_id=payload.categoria_id,
        codigo=payload.codigo,
        nombre=payload.nombre,
        descripcion=payload.descripcion,
        unidad_medida=payload.unidad_medida,
        estado="activo",
        fecha_alta=payload.fecha_alta,
        fecha_baja=payload.fecha_baja,
    )
    db.add(nuevo_activo)
    db.commit()
    db.refresh(nuevo_activo)

    ip = request.client.host if request.client else None
    registrar_evento_auditoria(
        db,
        usuario_id=current_user.id,
        accion="crear_activo",
        recurso="activo",
        recurso_id=nuevo_activo.id,
        resultado="exito",
        ip_origen=ip,
        detalle={
            "codigo": nuevo_activo.codigo,
            "nombre": nuevo_activo.nombre,
            "categoria_id": nuevo_activo.categoria_id,
        },
    )

    return nuevo_activo


@router.put("/{id}", response_model=ActivoOut)
def actualizar_activo(
    id: int,
    request: Request,
    payload: ActivoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles("Administrador", "Operador")),
):
    """Actualiza datos de un activo. Administrador y Operador."""
    activo = db.query(Activo).filter(Activo.id == id).first()
    if not activo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activo no encontrado",
        )

    if payload.categoria_id is not None and payload.categoria_id != activo.categoria_id:
        categoria = db.query(CategoriaActivo).filter(CategoriaActivo.id == payload.categoria_id).first()
        if not categoria:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La categoría especificada no existe",
            )
        activo.categoria_id = payload.categoria_id

    if payload.codigo is not None and payload.codigo != activo.codigo:
        existente_codigo = db.query(Activo).filter(Activo.codigo == payload.codigo, Activo.id != id).first()
        if existente_codigo:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe un activo con ese código",
            )
        activo.codigo = payload.codigo

    if payload.nombre is not None:
        activo.nombre = payload.nombre
    if payload.descripcion is not None:
        activo.descripcion = payload.descripcion
    if payload.unidad_medida is not None:
        activo.unidad_medida = payload.unidad_medida
    if "fecha_alta" in payload.model_fields_set:
        activo.fecha_alta = payload.fecha_alta
    if "fecha_baja" in payload.model_fields_set:
        activo.fecha_baja = payload.fecha_baja

    if activo.fecha_alta and activo.fecha_baja and activo.fecha_baja < activo.fecha_alta:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La fecha de baja no puede ser anterior a la fecha de alta",
        )

    db.commit()
    db.refresh(activo)

    ip = request.client.host if request.client else None
    registrar_evento_auditoria(
        db,
        usuario_id=current_user.id,
        accion="editar_activo",
        recurso="activo",
        recurso_id=activo.id,
        resultado="exito",
        ip_origen=ip,
        detalle={
            "codigo": activo.codigo,
            "nombre": activo.nombre,
            "categoria_id": activo.categoria_id,
        },
    )

    return activo


@router.patch("/{id}/desactivar", response_model=ActivoOut)
def desactivar_activo(
    id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles("Administrador", "Operador")),
):
    """Desactiva un activo (baja lógica). Administrador y Operador."""
    activo = db.query(Activo).filter(Activo.id == id).first()
    if not activo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activo no encontrado",
        )

    activo.estado = "baja"
    db.commit()
    db.refresh(activo)

    ip = request.client.host if request.client else None
    registrar_evento_auditoria(
        db,
        usuario_id=current_user.id,
        accion="desactivar_activo",
        recurso="activo",
        recurso_id=activo.id,
        resultado="exito",
        ip_origen=ip,
        detalle={"codigo": activo.codigo, "nombre": activo.nombre},
    )

    return activo


@router.patch("/{id}/reactivar", response_model=ActivoOut)
def reactivar_activo(
    id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles("Administrador", "Operador")),
):
    """Reactiva un activo en estado baja. Administrador y Operador."""
    activo = db.query(Activo).filter(Activo.id == id).first()
    if not activo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activo no encontrado",
        )

    activo.estado = "activo"
    db.commit()
    db.refresh(activo)

    ip = request.client.host if request.client else None
    registrar_evento_auditoria(
        db,
        usuario_id=current_user.id,
        accion="reactivar_activo",
        recurso="activo",
        recurso_id=activo.id,
        resultado="exito",
        ip_origen=ip,
        detalle={"codigo": activo.codigo, "nombre": activo.nombre},
    )

    return activo
