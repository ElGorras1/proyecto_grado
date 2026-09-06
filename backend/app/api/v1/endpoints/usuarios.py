from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.security import hash_password
from app.crud.auditoria import registrar_evento_auditoria
from app.db.session import get_db
from app.models.area import Area
from app.models.rol import Rol
from app.models.usuario import Usuario
from app.schemas.usuario import (
    CambiarPasswordRequest,
    RolOut,
    UsuarioCreate,
    UsuarioOut,
    UsuarioUpdate,
)

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


@router.get("/roles", response_model=list[RolOut])
def listar_roles(
    db: Session = Depends(get_db),
    _current_user: Usuario = Depends(require_roles("Administrador")),
):
    """Lista todos los roles activos disponibles en el sistema."""
    return db.query(Rol).filter(Rol.estado == "activo").order_by(Rol.id.asc()).all()


@router.get("", response_model=list[UsuarioOut])
def listar_usuarios(
    rol_id: int | None = Query(default=None),
    estado: str | None = Query(default=None),
    area_id: int | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    _current_user: Usuario = Depends(require_roles("Administrador")),
):
    """Lista usuarios con filtros opcionales y paginación."""
    query = db.query(Usuario)
    if rol_id is not None:
        query = query.filter(Usuario.rol_id == rol_id)
    if estado is not None:
        query = query.filter(Usuario.estado == estado)
    if area_id is not None:
        query = query.filter(Usuario.area_id == area_id)

    return query.order_by(Usuario.id.asc()).offset(skip).limit(limit).all()


@router.get("/{id}", response_model=UsuarioOut)
def obtener_usuario(
    id: int,
    db: Session = Depends(get_db),
    _current_user: Usuario = Depends(require_roles("Administrador")),
):
    """Obtiene el detalle de un usuario por su ID."""
    usuario = db.query(Usuario).filter(Usuario.id == id).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )
    return usuario


@router.post("", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED)
def crear_usuario(
    request: Request,
    payload: UsuarioCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles("Administrador")),
):
    """Crea un nuevo usuario en el sistema."""
    existente = db.query(Usuario).filter(Usuario.email == payload.email).first()
    if existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El email ya está registrado",
        )

    rol = db.query(Rol).filter(Rol.id == payload.rol_id).first()
    if not rol:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El rol especificado no existe",
        )

    if payload.area_id is not None:
        area = db.query(Area).filter(Area.id == payload.area_id).first()
        if not area:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El área especificada no existe",
            )

    nuevo_usuario = Usuario(
        nombre=payload.nombre,
        email=payload.email,
        password_hash=hash_password(payload.password),
        rol_id=payload.rol_id,
        area_id=payload.area_id,
        estado="activo",
    )
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)

    ip = request.client.host if request.client else None
    registrar_evento_auditoria(
        db,
        usuario_id=current_user.id,
        accion="crear_usuario",
        recurso="usuario",
        recurso_id=nuevo_usuario.id,
        resultado="exito",
        ip_origen=ip,
        detalle={"email": nuevo_usuario.email, "rol_id": nuevo_usuario.rol_id},
    )

    return nuevo_usuario


@router.put("/{id}", response_model=UsuarioOut)
def actualizar_usuario(
    id: int,
    request: Request,
    payload: UsuarioUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles("Administrador")),
):
    """Actualiza los datos de un usuario (excepto contraseña)."""
    usuario = db.query(Usuario).filter(Usuario.id == id).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    if payload.email is not None and payload.email != usuario.email:
        existente = db.query(Usuario).filter(Usuario.email == payload.email, Usuario.id != id).first()
        if existente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El email ya está registrado",
            )
        usuario.email = payload.email

    if payload.rol_id is not None:
        rol = db.query(Rol).filter(Rol.id == payload.rol_id).first()
        if not rol:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El rol especificado no existe",
            )
        usuario.rol_id = payload.rol_id

    if "area_id" in payload.model_fields_set:
        if payload.area_id is not None:
            area = db.query(Area).filter(Area.id == payload.area_id).first()
            if not area:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El área especificada no existe",
                )
        usuario.area_id = payload.area_id

    if payload.nombre is not None:
        usuario.nombre = payload.nombre

    db.commit()
    db.refresh(usuario)

    ip = request.client.host if request.client else None
    registrar_evento_auditoria(
        db,
        usuario_id=current_user.id,
        accion="editar_usuario",
        recurso="usuario",
        recurso_id=usuario.id,
        resultado="exito",
        ip_origen=ip,
        detalle={"email": usuario.email, "rol_id": usuario.rol_id},
    )

    return usuario


@router.patch("/{id}/desactivar", response_model=UsuarioOut)
def desactivar_usuario(
    id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles("Administrador")),
):
    """Desactiva un usuario (baja lógica). No permite auto-desactivación ni desactivar al último administrador."""
    usuario = db.query(Usuario).filter(Usuario.id == id).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    # Regla 1: Un Administrador no puede desactivarse a sí mismo
    if usuario.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puede desactivar su propia cuenta de Administrador",
        )

    # Regla 2: No permitir desactivar al último Administrador activo del sistema
    if usuario.rol.nombre == "Administrador" and usuario.estado == "activo":
        admin_rol = db.query(Rol).filter(Rol.nombre == "Administrador").first()
        admin_count = (
            db.query(Usuario)
            .filter(Usuario.rol_id == admin_rol.id, Usuario.estado == "activo")
            .count()
        )
        if admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se puede desactivar al último Administrador activo del sistema",
            )

    usuario.estado = "baja"
    db.commit()
    db.refresh(usuario)

    ip = request.client.host if request.client else None
    registrar_evento_auditoria(
        db,
        usuario_id=current_user.id,
        accion="desactivar_usuario",
        recurso="usuario",
        recurso_id=usuario.id,
        resultado="exito",
        ip_origen=ip,
        detalle={"usuario_desactivado": usuario.email},
    )

    return usuario


@router.patch("/{id}/reactivar", response_model=UsuarioOut)
def reactivar_usuario(
    id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles("Administrador")),
):
    """Reactiva un usuario que estaba en estado baja."""
    usuario = db.query(Usuario).filter(Usuario.id == id).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    usuario.estado = "activo"
    db.commit()
    db.refresh(usuario)

    ip = request.client.host if request.client else None
    registrar_evento_auditoria(
        db,
        usuario_id=current_user.id,
        accion="reactivar_usuario",
        recurso="usuario",
        recurso_id=usuario.id,
        resultado="exito",
        ip_origen=ip,
        detalle={"usuario_reactivado": usuario.email},
    )

    return usuario


@router.post("/{id}/resetear-password")
def resetear_password(
    id: int,
    request: Request,
    payload: CambiarPasswordRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_roles("Administrador")),
):
    """Restablece la contraseña de un usuario."""
    usuario = db.query(Usuario).filter(Usuario.id == id).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    usuario.password_hash = hash_password(payload.password_nuevo)
    db.commit()

    ip = request.client.host if request.client else None
    registrar_evento_auditoria(
        db,
        usuario_id=current_user.id,
        accion="resetear_password",
        recurso="usuario",
        recurso_id=usuario.id,
        resultado="exito",
        ip_origen=ip,
        detalle={"email": usuario.email},
    )

    return {"mensaje": "Contraseña restablecida exitosamente"}
