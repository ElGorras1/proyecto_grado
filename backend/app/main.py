from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.rate_limit import limiter
from app.api.v1.router import api_router
from app.db.session import get_db
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from app.services.trabajador_analitica import iniciar, detener


@asynccontextmanager
async def lifespan(_app: FastAPI):
    iniciar()
    try:
        yield
    finally:
        detener()


app = FastAPI(
    lifespan=lifespan,
    title=settings.PROJECT_NAME,
    version="0.1.0",
    description=(
        "API del Sistema Web de Gestión y Trazabilidad de Activos Operativos "
        "(Fundación Simón I. Patiño)."
    ),
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


from app.api.evidencia import router as evidencia_router
import os

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("storage/kardex_images", exist_ok=True)
app.include_router(evidencia_router)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["Sistema"])
def health_check():
    return {"status": "ok", "environment": settings.ENVIRONMENT}

@app.get("/health/ready", tags=["Sistema"])
def readiness(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        db.rollback()
        return JSONResponse(status_code=503, content={"status": "unavailable", "database": "error"})
    return {"status": "ok", "database": "ok"}
