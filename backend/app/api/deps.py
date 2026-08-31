from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.crud.usuario import get_usuario_by_id
from app.models.usuario import Usuario

# tokenUrl solo se usa para documentación (Swagger); el login real es JSON en /auth/login.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"/api/v1/auth/login", auto_error=False)


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

    usuario = get_usuario_by_id(db, int(payload["sub"]))
    if usuario is None or usuario.estado != "activo":
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
        if usuario.rol.nombre not in roles_permitidos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene privilegios suficientes para acceder a este recurso",
            )
        return usuario

    return verificador
