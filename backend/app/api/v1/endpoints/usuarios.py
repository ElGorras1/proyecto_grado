from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
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


def validar_rol(rol):
    if rol is None:
        raise HTTPException(400, "El rol especificado no existe")
    if rol.estado != "activo" or rol.nombre not in ("Administrador", "Operador", "Auditor"):
        raise HTTPException(409, "Selecciona un rol activo con permisos para este sistema")


def guardar_con_auditoria(db, usuario, **evento):
    """La cuenta y su constancia se confirman o revierten juntas."""
    try:
        db.flush()
        registrar_evento_auditoria(db, recurso="usuario", recurso_id=usuario.id,
                                  resultado="exito", commit=False, **evento)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Los datos de la cuenta entran en conflicto; revisa el email") from None
    except Exception:
        db.rollback()
        raise
    db.refresh(usuario)


def bloquear_administracion(db: Session, actual: Usuario):
    # Serializa bajas/cambios de rol: dos administradores no pueden retirarse
    # mutuamente los permisos y dejar el sistema sin administración.
    db.query(Rol).filter(Rol.nombre == "Administrador").with_for_update().all()
    actual = db.query(Usuario).filter_by(id=actual.id).populate_existing().first()
    if actual is None:
        raise HTTPException(403, "La cuenta administrativa ya no existe")
    db.expire(actual, ["rol"])
    if (
        actual.estado != "activo"
        or actual.rol is None
        or actual.rol.nombre != "Administrador"
        or actual.rol.estado != "activo"
    ):
        raise HTTPException(
            403, "Los permisos administrativos cambiaron. Inicia sesión nuevamente."
        )


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
    bloquear_administracion(db, current_user)
    existente = db.query(Usuario).filter(func.lower(Usuario.email) == str(payload.email).lower()).first()
    if existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El email ya está registrado",
        )

    rol = db.query(Rol).filter(Rol.id == payload.rol_id).first()
    validar_rol(rol)

    if payload.area_id is not None:
        area = db.query(Area).filter(Area.id == payload.area_id).populate_existing().with_for_update(read=True).first()
        if not area or area.estado != "activo":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El área especificada no existe o está de baja",
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

    ip = request.client.host if request.client else None
    guardar_con_auditoria(
        db, nuevo_usuario,
        usuario_id=current_user.id,
        accion="crear_usuario",
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
    bloquear_administracion(db, current_user)
    usuario = db.query(Usuario).filter(Usuario.id == id).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    if payload.email is not None and payload.email != usuario.email:
        existente = (
            db.query(Usuario).filter(func.lower(Usuario.email) == str(payload.email).lower(), Usuario.id != id).first()
        )
        if existente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El email ya está registrado",
            )
        usuario.email = payload.email

    if payload.rol_id is not None:
        rol = db.query(Rol).filter(Rol.id == payload.rol_id).first()
        validar_rol(rol)
        if usuario.id == current_user.id and rol.nombre != "Administrador":
            raise HTTPException(400, "No puede quitar el rol Administrador de su propia cuenta")
        usuario.rol_id = payload.rol_id

    if "area_id" in payload.model_fields_set:
        if payload.area_id is not None:
            area = db.query(Area).filter(Area.id == payload.area_id).populate_existing().with_for_update(read=True).first()
            if not area or area.estado != "activo":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El área especificada no existe o está de baja",
                )
        usuario.area_id = payload.area_id

    if payload.nombre is not None:
        usuario.nombre = payload.nombre

    ip = request.client.host if request.client else None
    guardar_con_auditoria(
        db, usuario,
        usuario_id=current_user.id,
        accion="editar_usuario",
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
    """Baja lógica; protege la propia cuenta y al último administrador."""
    bloquear_administracion(db, current_user)
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

    ip = request.client.host if request.client else None
    guardar_con_auditoria(
        db, usuario,
        usuario_id=current_user.id,
        accion="desactivar_usuario",
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
    bloquear_administracion(db, current_user)
    usuario = db.query(Usuario).filter(Usuario.id == id).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    validar_rol(usuario.rol)
    if usuario.area_id is not None:
        area = db.query(Area).filter_by(id=usuario.area_id).populate_existing().with_for_update(read=True).first()
        if area is None or area.estado != "activo":
            raise HTTPException(409, "Reasigna la cuenta a un área activa o retira su adscripción antes de reactivarla")
    usuario.estado = "activo"

    ip = request.client.host if request.client else None
    guardar_con_auditoria(
        db, usuario,
        usuario_id=current_user.id,
        accion="reactivar_usuario",
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
    bloquear_administracion(db, current_user)
    usuario = db.query(Usuario).filter(Usuario.id == id).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    usuario.password_hash = hash_password(payload.password_nuevo)

    ip = request.client.host if request.client else None
    guardar_con_auditoria(
        db, usuario,
        usuario_id=current_user.id,
        accion="resetear_password",
        ip_origen=ip,
        detalle={"email": usuario.email},
    )

    return {"mensaje": "Contraseña restablecida exitosamente"}
