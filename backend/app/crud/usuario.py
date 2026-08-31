from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.usuario import Usuario
from app.core.security import verify_password


def get_usuario_by_email(db: Session, email: str) -> Usuario | None:
    return db.query(Usuario).filter(Usuario.email == email, Usuario.estado == "activo").first()


def get_usuario_by_id(db: Session, usuario_id: int) -> Usuario | None:
    return db.query(Usuario).filter(Usuario.id == usuario_id).first()


def authenticate(db: Session, email: str, password: str) -> Usuario | None:
    """
    Devuelve el usuario si las credenciales son válidas y el estado es 'activo'.
    Devuelve None en cualquier otro caso (usuario inexistente, contraseña
    incorrecta o usuario dado de baja).
    """
    usuario = get_usuario_by_email(db, email)
    if not usuario:
        return None
    if not verify_password(password, usuario.password_hash):
        return None
    return usuario


def registrar_login_exitoso(db: Session, usuario: Usuario) -> None:
    usuario.last_login_at = datetime.now(timezone.utc)
    db.add(usuario)
    db.commit()
