from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    auditoria,
    usuarios,
    areas,
    categorias,
    activos,
    existencias,
    inventario,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(auditoria.router)
api_router.include_router(usuarios.router)
api_router.include_router(areas.router)
api_router.include_router(categorias.router)
api_router.include_router(activos.router)
api_router.include_router(existencias.router)
api_router.include_router(inventario.router)
