"""
Crea usuarios de prueba para los 3 roles, útil para demostrar RBAC en
la presentación (Administrador ya lo tienes con seed_admin.py).

Uso (desde backend/, con el entorno virtual activado):
    python -m scripts.seed_test_users
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.db.session import SessionLocal
from app.models.rol import Rol
from app.models.usuario import Usuario
from app.core.security import hash_password

USUARIOS_DEMO = [
    ("Operador", "Operador de Prueba", "operador@simonpatino.com"),
    ("Auditor", "Auditor de Prueba", "auditor@simonpatino.com"),
]

PASSWORD_DEMO = "DemoPassword123!"


def main():
    db = SessionLocal()
    try:
        for nombre_rol, nombre_usuario, email in USUARIOS_DEMO:
            rol = db.query(Rol).filter(Rol.nombre == nombre_rol).first()
            if rol is None:
                print(f"ERROR: no existe el rol '{nombre_rol}'")
                continue

            existente = db.query(Usuario).filter(Usuario.email == email).first()
            if existente:
                print(f"Ya existe: {email}")
                continue

            usuario = Usuario(
                rol_id=rol.id,
                nombre=nombre_usuario,
                email=email,
                password_hash=hash_password(PASSWORD_DEMO),
                estado="activo",
            )
            db.add(usuario)
            db.commit()
            print(f"Creado: {email} / {PASSWORD_DEMO} (rol: {nombre_rol})")
    finally:
        db.close()


if __name__ == "__main__":
    main()
