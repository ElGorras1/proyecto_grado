"""Libera una solicitud huérfana tras detener el servidor y comprobar que no creó lote."""

import argparse
import socket
from datetime import UTC, datetime

from sqlalchemy import func, update

from app.db.session import SessionLocal
from app.models.auditoria import AuditoriaSistema
from app.models.kardex import MovimientoKardex, SolicitudCargaKardex


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("solicitud_id", type=int)
    parser.add_argument("articulo_id", type=int)
    args = parser.parse_args()
    try:
        with socket.create_connection(("127.0.0.1", 8000), timeout=2):
            pass
    except (ConnectionRefusedError, TimeoutError):
        pass
    else:
        raise RuntimeError("Detén primero el servidor que podría estar procesando la carga")
    with SessionLocal() as db:
        solicitud = db.get(SolicitudCargaKardex, args.solicitud_id)
        if not solicitud or solicitud.articulo_id != args.articulo_id:
            raise RuntimeError("La solicitud no coincide con el artículo indicado")
        if solicitud.estado != "PROCESANDO" or solicitud.lote_id or solicitud.pendiente_id:
            raise RuntimeError("La solicitud cambió de estado o ya creó un lote")
        cantidad = db.query(func.count(MovimientoKardex.id)).filter_by(
            articulo_id=args.articulo_id).scalar()
        if cantidad:
            raise RuntimeError("El artículo ya tiene movimientos; requiere revisión manual")
        modificadas = db.execute(update(SolicitudCargaKardex).where(
            SolicitudCargaKardex.id == args.solicitud_id,
            SolicitudCargaKardex.estado == "PROCESANDO",
            SolicitudCargaKardex.lote_id.is_(None),
            SolicitudCargaKardex.pendiente_id.is_(None),
        ).values(estado="FALLIDO")).rowcount
        if modificadas != 1:
            raise RuntimeError("La solicitud cambió mientras se recuperaba")
        db.add(AuditoriaSistema(
            usuario_id=None, accion="recuperar_carga_kardex",
            recurso="solicitudes_carga_kardex", recurso_id=args.solicitud_id,
            resultado="exito", fecha_hora=datetime.now(UTC), ip_origen=None,
            detalle={"articulo_id": args.articulo_id,
                     "motivo": "servidor detenido tras timeout del importador; sin lote ni movimientos"},
        ))
        db.commit()
    print(f"Solicitud {args.solicitud_id} recuperada para reintento con las mismas fotos")


if __name__ == "__main__":
    main()
