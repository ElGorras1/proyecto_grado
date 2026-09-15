from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.auth import LoginRequest, TokenResponse, UsuarioMe
from app.crud.usuario import authenticate, registrar_login_exitoso, get_usuario_by_email
from app.crud.auditoria import registrar_evento_auditoria
from app.core.security import create_access_token, verify_password
from app.api.deps import get_current_user, require_roles
from app.models.usuario import Usuario
from app.core.rate_limit import limiter

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/5minutes")
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)):
    # Buscar usuario y verificar contraseña por separado para poder
    # registrar en auditoría si el usuario existía o no.
    usuario = get_usuario_by_email(db, payload.email)
    ip = request.client.host if request.client else None

    if usuario is None:
        # Login fallido: usuario desconocido
        registrar_evento_auditoria(
            db,
            usuario_id=None,
            accion="login",
            recurso="usuario",
            recurso_id=None,
            resultado="rechazo",
            ip_origen=ip,
            detalle={"email_intentado": payload.email, "razon": "Usuario inexistente"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
        )

    if usuario.estado != "activo":
        # Login fallido: cuenta desactivada
        etiqueta = f"{usuario.rol.nombre}/{usuario.estado.capitalize()}" if usuario.rol else f"/{usuario.estado.capitalize()}"
        registrar_evento_auditoria(
            db,
            usuario_id=usuario.id,
            accion="login",
            recurso="usuario",
            recurso_id=usuario.id,
            resultado="rechazo",
            ip_origen=ip,
            detalle={
                "email_intentado": payload.email,
                "razon": "Cuenta desactivada",
                "usuario_nombre": usuario.nombre,
                "usuario_etiqueta": etiqueta
            },
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cuenta desactivada",
        )

    if not verify_password(payload.password, usuario.password_hash):
        # Login fallido: contraseña incorrecta
        registrar_evento_auditoria(
            db,
            usuario_id=usuario.id,
            accion="login",
            recurso="usuario",
            recurso_id=usuario.id,
            resultado="rechazo",
            ip_origen=ip,
            detalle={"email_intentado": payload.email, "razon": "Contraseña incorrecta"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
        )

    # Login exitoso: registrar en auditoría y actualizar last_login_at.
    registrar_evento_auditoria(
        db,
        usuario_id=usuario.id,
        accion="login",
        recurso="usuario",
        recurso_id=usuario.id,
        resultado="exito",
        ip_origen=ip,
    )
    registrar_login_exitoso(db, usuario)

    token = create_access_token(
        subject=usuario.id,
        extra_claims={"rol": usuario.rol.nombre},
    )
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UsuarioMe)
def leer_usuario_actual(usuario: Usuario = Depends(get_current_user)):
    return UsuarioMe(
        id=usuario.id,
        nombre=usuario.nombre,
        email=usuario.email,
        rol=usuario.rol.nombre,
        area_id=usuario.area_id,
    )


@router.get("/admin/ping")
def solo_administrador(usuario: Usuario = Depends(require_roles("Administrador"))):
    """
    Endpoint de ejemplo: solo accesible por el rol Administrador.
    Úsalo para verificar que un Operador/Auditor recibe 403 aquí,
    y que un usuario no autenticado recibe 401.
    """
    return {"mensaje": f"Hola {usuario.nombre}, acceso administrativo confirmado"}
