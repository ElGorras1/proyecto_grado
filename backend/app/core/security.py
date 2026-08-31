from datetime import datetime, timedelta, timezone
from typing import Any

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError
from jose import jwt, JWTError

from app.core.config import settings

# Argon2id por defecto (recomendado por OWASP): resistente a ataques por GPU/ASIC.
_ph = PasswordHasher()


def hash_password(password: str) -> str:
    """Genera el hash Argon2 de una contraseña en texto plano."""
    return _ph.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verifica una contraseña contra su hash Argon2 almacenado."""
    try:
        return _ph.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def create_access_token(subject: str | int, extra_claims: dict[str, Any] | None = None) -> str:
    """
    Crea un JWT firmado.
    'subject' es normalmente el id del usuario (usuario.id).
    'extra_claims' permite incluir rol/permisos en el propio token para
    evitar consultas repetidas (ej: {"rol": "Administrador"}).
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode: dict[str, Any] = {"sub": str(subject), "exp": expire}
    if extra_claims:
        to_encode.update(extra_claims)
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any] | None:
    """Decodifica y valida un JWT. Devuelve None si es inválido o expiró."""
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None
