from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.kardex import MovimientoKardex
from app.services.clasificador_nodos import clasificar_nodo_movimiento

def backfill_nodos():
    db = SessionLocal()
    movimientos = db.query(MovimientoKardex).all()
    count = 0
    for mov in movimientos:
        if mov.nodo_grafo is None:
            nodo_grafo, req_auditoria = clasificar_nodo_movimiento(
                detalle=mov.detalle,
                ref=mov.referencia,
                area=mov.area,
                ingreso=mov.ingresos,
                salida=mov.salidas
            )
            mov.nodo_grafo = nodo_grafo
            # If it had no node before, we assign it and update audit flag
            mov.requiere_auditoria_nodo = req_auditoria
            count += 1
            
    db.commit()
    db.close()
    print(f"Backfill completado. {count} filas actualizadas.")

if __name__ == "__main__":
    backfill_nodos()
