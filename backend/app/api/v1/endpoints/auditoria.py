from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.deps import require_roles
from app.models.auditoria import AuditoriaSistema
from app.schemas.auditoria import AuditoriaAccesoOut

router = APIRouter(prefix="/auditoria", tags=["Auditoría"])


@router.get("/accesos", response_model=list[AuditoriaAccesoOut])
def listar_accesos(
    usuario_id: int | None = None,
    resultado: str | None = None,
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    _usuario=Depends(require_roles("Administrador", "Auditor")),
):
    """Reporte de accesos (intentos de login) — solo Administrador y Auditor."""
    query = db.query(AuditoriaSistema).filter(AuditoriaSistema.accion == "login")

    if usuario_id is not None:
        query = query.filter(AuditoriaSistema.usuario_id == usuario_id)
    if resultado is not None:
        query = query.filter(AuditoriaSistema.resultado == resultado)
    if fecha_desde is not None:
        query = query.filter(AuditoriaSistema.fecha_hora >= fecha_desde)
    if fecha_hasta is not None:
        from datetime import datetime, time, timezone

        fin_del_dia = datetime.combine(fecha_hasta, time.max, tzinfo=timezone.utc)
        query = query.filter(AuditoriaSistema.fecha_hora <= fin_del_dia)

    query = query.order_by(AuditoriaSistema.fecha_hora.desc())
    return query.offset(skip).limit(limit).all()
