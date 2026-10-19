from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class EntrenamientoHistorico(BaseModel):
    semilla: int = Field(42, ge=0, le=2147483646)
    arboles: int = Field(200, ge=100, le=500)
    porcentaje_revision: float = Field(5, ge=1, le=20)
    excluir_articulos: list[int] = Field(default_factory=list, max_length=1000)
    modo: Literal["RETROSPECTIVO", "TEMPORAL"] = "RETROSPECTIVO"
    gestion_evaluacion: int | None = Field(default=None, ge=1902, le=9998)

    @model_validator(mode="after")
    def validar_temporal(self):
        from datetime import datetime
        from zoneinfo import ZoneInfo

        if self.modo == "TEMPORAL":
            actual = datetime.now(ZoneInfo("America/La_Paz")).year
            if self.gestion_evaluacion is None or self.gestion_evaluacion >= actual:
                raise ValueError("La evaluación temporal necesita un año documental ya concluido.")
        elif self.gestion_evaluacion is not None:
            raise ValueError("El año reservado solo corresponde a evaluación temporal.")
        return self


class RevisionAnalitica(BaseModel):
    estado: Literal["EN_REVISION", "JUSTIFICADO", "REQUIERE_SEGUIMIENTO", "CERRADO"]
    motivo: str = Field(min_length=10, max_length=4000)
    etiqueta: Literal["INUSUAL_RELEVANTE", "LEGITIMO", "ERROR_DOCUMENTAL", "NO_CONCLUYENTE"]
    revision_esperada: int = Field(ge=0)

    @field_validator("motivo")
    @classmethod
    def motivo_no_vacio(cls, value):
        value = value.strip()
        if len(value) < 10:
            raise ValueError("Explica el motivo con al menos diez caracteres.")
        return value
