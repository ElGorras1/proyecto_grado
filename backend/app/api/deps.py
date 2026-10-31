import hmac

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token, huella_credencial
from app.crud.usuario import get_usuario_by_id
from app.db.session import get_db
from app.models.usuario import Usuario

# tokenUrl solo se usa para documentación (Swagger); el login real es JSON en /auth/login.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    """
    Valida el JWT recibido en el header Authorization: Bearer <token>.
    - Sin token o token inválido/expirado -> 401.
    - Usuario no encontrado o dado de baja -> 401.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No autenticado o token inválido",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if token is None:
        raise credentials_exception

    payload = decode_access_token(token)
    if payload is None or "sub" not in payload:
        raise credentials_exception

    try:
        usuario_id = int(payload["sub"])
    except (ValueError, TypeError, OverflowError):
        raise credentials_exception from None
    usuario = get_usuario_by_id(db, usuario_id)
    if (
        usuario is None
        or usuario.estado != "activo"
        or usuario.rol is None
        or usuario.rol.estado != "activo"
    ):
        raise credentials_exception

    if usuario.rol.nombre not in ("Administrador", "Operador", "Auditor"):
        raise HTTPException(status_code=403, detail="Rol sin permisos para este sistema")

    # Los inicios de sesión nuevos incluyen esta huella. Un restablecimiento
    # invalida el Bearer y la cookie de fotos sin reescribir las cuentas.
    # Los JWT anteriores a esta actualización caducan con su plazo original.
    if "credencial" in payload:
        huella = payload["credencial"]
        if not isinstance(huella, str) or not hmac.compare_digest(huella.encode(), huella_credencial(usuario.password_hash).encode()):
            raise credentials_exception

    return usuario


def require_roles(*roles_permitidos: str):
    """
    Fábrica de dependencias para proteger endpoints por rol (RBAC).

    Uso:
        @router.get("/admin/usuarios")
        def listar_usuarios(usuario = Depends(require_roles("Administrador"))):
            ...

    Si el usuario está autenticado pero su rol no está en 'roles_permitidos',
    se responde 403 (no 401: ya sabemos quién es, solo no tiene privilegios).
    """

    def verificador(usuario: Usuario = Depends(get_current_user)) -> Usuario:
        if usuario.rol is None or usuario.rol.nombre not in roles_permitidos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene privilegios suficientes para acceder a este recurso",
            )
        return usuario

    return verificador
