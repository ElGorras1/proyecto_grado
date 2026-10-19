"""Prueba concurrencia exclusivamente en una copia creada por preparar_apertura."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from starlette.requests import Request
from fastapi import HTTPException
from app.db.session import engine
from app.models.activos import Activo, CategoriaActivo
from app.models.usuario import Usuario
from app.models.rol import Rol
from app.models.inventario import AperturaInventario
from app.api.v1.endpoints.kardex import aprobar_apertura, registrar_movimiento_actual, anular_movimiento_actual, AperturaCrear, MovimientoActualCrear


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", required=True)
    args = parser.parse_args()
    if not args.database.startswith("activos_apertura_qa_") or args.database == engine.url.database:
        raise RuntimeError("Solo se permite una copia QA de apertura")
    copia = create_engine(engine.url.set(database=args.database))
    with Session(copia) as db:
        usuario_id = db.scalar(select(Usuario.id).join(Rol).where(Rol.nombre == "Administrador", Usuario.estado == "activo").limit(1))
        cat = CategoriaActivo(nombre="QA apertura " + str(uuid4()))
        db.add(cat); db.flush()
        art = Activo(categoria_id=cat.id, codigo="QA-" + str(uuid4()), nombre="Prueba aislada de concurrencia")
        db.add(art); db.commit(); articulo_id = art.id
    request = Request({"type": "http", "client": ("127.0.0.1", 0)})
    def competir(accion):
        barrera = Barrier(2)
        def ejecutar(_):
            with Session(copia) as db:
                usuario = db.get(Usuario, usuario_id)
                barrera.wait(timeout=10)
                try:
                    resultado = accion(db, usuario)
                    return 200, resultado
                except HTTPException as exc:
                    db.rollback()
                    return exc.status_code, None
        with ThreadPoolExecutor(max_workers=2) as pool:
            return list(pool.map(ejecutar, range(2)))
    resultados = competir(lambda db, u: aprobar_apertura(articulo_id,
        AperturaCrear(cantidad=5, referencia_documento="QA-01", justificacion="Conteo ficticio en copia aislada", conteo_verificado=True), request, db, u))
    assert sorted(x[0] for x in resultados) == [200, 409], resultados
    resultados = competir(lambda db, u: registrar_movimiento_actual(request,
        MovimientoActualCrear(articulo_id=articulo_id, tipo="salida", cantidad=4, nodo_grafo="Ventas"), db, u).id)
    assert sorted(x[0] for x in resultados) == [200, 400], resultados
    movimiento_id = next(x[1] for x in resultados if x[0] == 200)
    with Session(copia) as db:
        assert db.get(AperturaInventario, articulo_id).cantidad_actual == 1
    resultados = competir(lambda db, u: anular_movimiento_actual(request, movimiento_id, db, u).id)
    assert sorted(x[0] for x in resultados) == [200, 400], resultados
    with Session(copia) as db:
        assert db.get(AperturaInventario, articulo_id).cantidad_actual == 5
    print("PostgreSQL QA: apertura única, salidas simultáneas y doble anulación correctas.")

if __name__ == "__main__":
    main()
