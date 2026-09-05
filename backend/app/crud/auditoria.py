from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.auditoria import AuditoriaSistema


def registrar_evento_auditoria(
    db: Session,
    *,
    usuario_id: int | None,
    accion: str,
    recurso: str,
    recurso_id: int | None,
    resultado: str,
    ip_origen: str | None,
    detalle: dict[str, Any] | None = None,
) -> AuditoriaSistema:
    """Crea un registro en auditoria_sistema y lo persiste."""
    registro = AuditoriaSistema(
        usuario_id=usuario_id,
        accion=accion,
        recurso=recurso,
        recurso_id=recurso_id,
        resultado=resultado,
        fecha_hora=datetime.now(timezone.utc),
        ip_origen=ip_origen,
        detalle=detalle,
    )
    db.add(registro)
    db.commit()
    db.refresh(registro)
    return registro
