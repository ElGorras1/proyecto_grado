from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.auth import LoginRequest, TokenResponse, UsuarioMe
from app.crud.usuario import authenticate, registrar_login_exitoso
from app.core.security import create_access_token
from app.api.deps import get_current_user, require_roles
from app.models.usuario import Usuario

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    usuario = authenticate(db, payload.email, payload.password)
    if usuario is None:
        # Mensaje genérico: no revelar si el email existe o no (buena práctica de seguridad).
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
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
