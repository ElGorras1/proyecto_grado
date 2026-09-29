from fastapi import APIRouter

from app.api.v1.endpoints import auth, auditoria, usuarios, kardex, reportes, dashboard

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(auditoria.router)
api_router.include_router(usuarios.router)
api_router.include_router(kardex.router, prefix="/kardex", tags=["Kardex"])
api_router.include_router(reportes.router)
api_router.include_router(dashboard.router)
