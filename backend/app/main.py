from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.rate_limit import limiter
from app.api.v1.router import api_router


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    description=(
        "API del Sistema Web de Gestión y Trazabilidad de Activos Operativos "
        "(Fundación Simón I. Patiño)."
    ),
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


from fastapi.staticfiles import StaticFiles
import os

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("storage/kardex_images", exist_ok=True)
app.mount("/storage", StaticFiles(directory="storage"), name="storage")

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["Sistema"])
def health_check():
    return {"status": "ok", "environment": settings.ENVIRONMENT}
