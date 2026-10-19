"""Primer Administrador: contraseña interactiva; no cambia cuentas existentes."""

import argparse
from getpass import getpass

from pydantic import EmailStr, TypeAdapter

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.rol import Rol
from app.models.usuario import Usuario


def crear(db, email, password, nombre):
    email = str(TypeAdapter(EmailStr).validate_python(email))
    if len(password) < 12:
        raise ValueError("La contraseña inicial debe tener al menos doce caracteres.")
    if not nombre.strip():
        raise ValueError("Indica el nombre del administrador.")
    if (
        db.query(Usuario)
        .join(Rol)
        .filter(Rol.nombre == "Administrador", Usuario.estado == "activo")
        .first()
    ):
        raise ValueError(
            "Ya existe un Administrador activo; gestiona las cuentas desde el sistema."
        )
    if db.query(Usuario).filter_by(email=email).first():
        raise ValueError("Ese correo ya existe; no se cambia su contraseña ni su rol.")
    roles = {}
    for nombre_rol in ("Administrador", "Operador", "Auditor"):
        r = db.query(Rol).filter_by(nombre=nombre_rol).first()
        if r is None:
            r = Rol(nombre=nombre_rol, estado="activo")
            db.add(r)
            db.flush()
        if r.estado != "activo":
            raise ValueError(
                "Hay un rol desactivado; revisa su configuración antes de inicializar."
            )
        roles[nombre_rol] = r
    u = Usuario(
        rol_id=roles["Administrador"].id,
        nombre=nombre.strip(),
        email=email,
        password_hash=hash_password(password),
        estado="activo",
    )
    db.add(u)
    db.commit()
    return u.id


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", required=True)
    parser.add_argument("--nombre", required=True)
    args = parser.parse_args()
    password = getpass("Contraseña inicial (no se muestra): ")
    if password != getpass("Repite la contraseña: "):
        raise SystemExit("Las contraseñas no coinciden; no se creó ninguna cuenta.")
    with SessionLocal() as db:
        try:
            id = crear(db, args.email, password, args.nombre)
        except ValueError as e:
            db.rollback()
            raise SystemExit(str(e)) from None
    print(f"Administrador inicial creado, id {id}. La contraseña permanece privada.")


if __name__ == "__main__":
    main()
