"""
Crea el primer usuario Administrador para poder iniciar sesión.

Uso (desde la carpeta backend/, con el entorno virtual activado):
    python -m scripts.seed_admin
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.db.session import SessionLocal
from app.models.rol import Rol
from app.models.usuario import Usuario
from app.core.security import hash_password


def main():
    db = SessionLocal()
    try:
        rol_admin = db.query(Rol).filter(Rol.nombre == "Administrador").first()
        if rol_admin is None:
            print("ERROR: no existe el rol 'Administrador'. Ejecuta primero initial_schema.sql")
            return

        email = "admin@simonpatino.test"
        existente = db.query(Usuario).filter(Usuario.email == email).first()
        if existente:
            print(f"Ya existe un usuario con email {email}")
            return

        usuario = Usuario(
            rol_id=rol_admin.id,
            nombre="Administrador General",
            email=email,
            password_hash=hash_password("CambiarPassword123!"),
            estado="activo",
        )
        db.add(usuario)
        db.commit()
        print(f"Usuario administrador creado: {email} / CambiarPassword123!")
        print("Cámbiala apenas inicies sesión.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
