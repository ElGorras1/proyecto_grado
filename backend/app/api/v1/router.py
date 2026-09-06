from fastapi import APIRouter

from app.api.v1.endpoints import auth, auditoria, usuarios, areas

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(auditoria.router)
api_router.include_router(usuarios.router)
api_router.include_router(areas.router)

# A medida que avances con los Sprints 2-5, se agregan aquí:
# api_router.include_router(activos.router)
# api_router.include_router(movimientos.router)
# api_router.include_router(trazabilidad.router)
