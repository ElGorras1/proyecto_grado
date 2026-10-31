from fastapi import APIRouter

from app.api.v1.endpoints import auth, auditoria, usuarios, kardex, reportes, dashboard, muestra_hil, conciliacion, transferencias, kardex_digital, custodias_externas, ajustes_operativos

api_router = APIRouter()
from app.api.v1.endpoints import documentos_operativos
api_router.include_router(documentos_operativos.router)
api_router.include_router(auth.router)
api_router.include_router(auditoria.router)
api_router.include_router(usuarios.router)
api_router.include_router(kardex.router, prefix="/kardex", tags=["Kardex"])
api_router.include_router(muestra_hil.router)
api_router.include_router(conciliacion.router)
api_router.include_router(transferencias.router)
api_router.include_router(kardex_digital.router)
api_router.include_router(custodias_externas.router)
api_router.include_router(ajustes_operativos.router)
api_router.include_router(reportes.router)
api_router.include_router(dashboard.router)

from app.api.v1.endpoints import analitica
api_router.include_router(analitica.router)
from app.api.v1.endpoints import reglas_historicas
api_router.include_router(reglas_historicas.router)
from app.api.v1.endpoints import cobertura
api_router.include_router(cobertura.router)
from app.api.v1.endpoints import trazabilidad
api_router.include_router(trazabilidad.router)
from app.api.v1.endpoints import control_alertas
api_router.include_router(control_alertas.router)
from app.api.v1.endpoints import analitica_operativa
api_router.include_router(analitica_operativa.router)
from app.api.v1.endpoints import cierre_anual
api_router.include_router(cierre_anual.router)
from app.api.v1.endpoints import reporte_institucional
api_router.include_router(reporte_institucional.router)
from app.api.v1.endpoints import administracion_areas
api_router.include_router(administracion_areas.router)
from app.api.v1.endpoints import rectificaciones_logisticas
api_router.include_router(rectificaciones_logisticas.router)
from app.api.v1.endpoints import preparacion_inventario
api_router.include_router(preparacion_inventario.router)
from app.api.v1.endpoints import validacion_independiente
api_router.include_router(validacion_independiente.router)
