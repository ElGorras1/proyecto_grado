from pydantic import BaseModel, ConfigDict, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UsuarioMe(BaseModel):
    id: int
    nombre: str
    email: EmailStr
    rol: str
    area_id: int | None = None

    model_config = ConfigDict(from_attributes=True)
