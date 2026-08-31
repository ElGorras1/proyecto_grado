from datetime import datetime
from typing import Any

from sqlalchemy import String, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Alerta(Base):
    """Alerta automática generada por una regla determinística o por Isolation Forest."""

    __tablename__ = "alerta"

    id: Mapped[int] = mapped_column(primary_key=True)
    movimiento_id: Mapped[int] = mapped_column(ForeignKey("movimiento.id"), nullable=False)
    resultado_regla_id: Mapped[int | None] = mapped_column(ForeignKey("resultado_regla.id"))
    evaluacion_anomalia_id: Mapped[int | None] = mapped_column(ForeignKey("evaluacion_anomalia.id"))
    tipo_alerta: Mapped[str] = mapped_column(String(50), nullable=False)
    prioridad: Mapped[str] = mapped_column(String(20), default="media")
    estado: Mapped[str] = mapped_column(String(30), default="generada")
    titulo: Mapped[str] = mapped_column(String(255), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text)
    generada_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revisada_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revisada_por: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"))


class CasoAuditoria(Base):
    """Caso abierto por un auditor a partir de una alerta (flujo HITL de auditoría)."""

    __tablename__ = "caso_auditoria"

    id: Mapped[int] = mapped_column(primary_key=True)
    alerta_id: Mapped[int] = mapped_column(ForeignKey("alerta.id"), nullable=False)
    auditor_id: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"))
    estado_caso: Mapped[str] = mapped_column(String(30), default="nuevo")
    prioridad: Mapped[str | None] = mapped_column(String(20))
    fecha_apertura: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    fecha_cierre: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    conclusion: Mapped[str | None] = mapped_column(Text)


class RevisionCaso(Base):
    """Historial de cambios de estado de un caso de auditoría."""

    __tablename__ = "revision_caso"

    id: Mapped[int] = mapped_column(primary_key=True)
    caso_id: Mapped[int] = mapped_column(ForeignKey("caso_auditoria.id"), nullable=False)
    auditor_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"), nullable=False)
    estado_anterior: Mapped[str | None] = mapped_column(String(30))
    estado_nuevo: Mapped[str] = mapped_column(String(30), nullable=False)
    comentario: Mapped[str | None] = mapped_column(Text)
    evidencia_ref: Mapped[str | None] = mapped_column(Text)
    revisado_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class AuditoriaSistema(Base):
    """Log general de acciones del sistema (accesos, altas/bajas, decisiones)."""

    __tablename__ = "auditoria_sistema"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"))
    accion: Mapped[str] = mapped_column(String(50), nullable=False)
    recurso: Mapped[str] = mapped_column(String(100), nullable=False)
    recurso_id: Mapped[int | None] = mapped_column()
    resultado: Mapped[str] = mapped_column(String(20), nullable=False)  # exito/rechazo/error
    fecha_hora: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ip_origen: Mapped[str | None] = mapped_column(String(45))  # INET en Postgres, String en ORM
    detalle: Mapped[dict[str, Any] | None] = mapped_column(JSON)
