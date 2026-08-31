from sqlalchemy import ForeignKey, Table, Column, BigInteger

from app.db.session import Base

# Tabla puente pura (rol_id, permiso_id) tal como está en initial_schema.sql.
rol_permiso = Table(
    "rol_permiso",
    Base.metadata,
    Column("rol_id", BigInteger, ForeignKey("rol.id"), primary_key=True),
    Column("permiso_id", BigInteger, ForeignKey("permiso.id"), primary_key=True),
    extend_existing=True,
)
