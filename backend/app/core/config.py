from typing import Literal
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configuración central de la aplicación.
    Todos los valores se leen desde el archivo .env (ver .env.example).
    """

    PROJECT_NAME: str = "Sistema de Gestión y Trazabilidad de Activos Operativos"
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: Literal["HS256"] = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60, gt=0, le=1440)

    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    ENVIRONMENT: Literal["development", "test", "production"] = "development"
    GEMINI_API_KEY: str | None = None
    KARDEX_TANDA_ACTUAL: int = Field(default=3, ge=1, le=9999)
    KARDEX_MAX_PAGINAS: int = Field(default=20, gt=0)
    KARDEX_MAX_MB_IMAGEN: int = Field(default=20, gt=0)
    KARDEX_MAX_MB_LOTE: int = Field(default=100, gt=0)
    KARDEX_MAX_MEGAPIXELES: int = Field(default=60, gt=0)
    CONTROL_HORA_INICIO: int = Field(default=7, ge=0, le=23)
    CONTROL_HORA_FIN: int = Field(default=20, ge=1, le=24)
    CONTROL_CANTIDAD_EXTREMA: int = Field(default=1000, ge=1)
    CONTROL_PORCENTAJE_MAYORITARIO: int = Field(default=80, ge=1, le=100)
    CONTROL_STOCK_MINIMO_MAYORITARIO: int = Field(default=10, ge=1)
    CONTROL_FACTOR_ATIPICO: int = Field(default=3, ge=2, le=100)
    CONTROL_MIN_COMPARABLES: int = Field(default=5, ge=2, le=20)
    CONTROL_MIN_CANTIDAD_ATIPICA: int = Field(default=10, ge=1)
    CONTROL_REPETICION_MINUTOS: int = Field(default=5, ge=1, le=60)
    CONTROL_REGISTRO_TARDIO_HORAS: int = Field(default=24, ge=1)

    @model_validator(mode="after")
    def validar_horario_control(self):
        if self.CONTROL_HORA_INICIO >= self.CONTROL_HORA_FIN:
            raise ValueError("CONTROL_HORA_INICIO debe ser menor que CONTROL_HORA_FIN")
        if self.ENVIRONMENT == "production":
            secreto = self.JWT_SECRET_KEY
            if len(secreto.encode()) < 32 or any(s in secreto.lower() for s in ("changeme", "cambia", "change-me")):
                raise ValueError("Producción requiere una clave JWT privada de al menos 32 bytes")
            if not self.BACKEND_CORS_ORIGINS or "*" in self.BACKEND_CORS_ORIGINS:
                raise ValueError("Producción requiere orígenes CORS explícitos")
        return self

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
