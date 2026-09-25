from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterIn(BaseModel):
    nome: str = Field(min_length=1, max_length=255)
    email: EmailStr
    senha: str = Field(min_length=8, max_length=72)


class LoginIn(BaseModel):
    email: EmailStr
    senha: str


class UsuarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    email: str
    role: str
    criado_em: datetime


class UsuarioPublicoOut(BaseModel):
    """Só o que pode aparecer num perfil público (atividade 6) — sem
    e-mail nem papel."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RoleUpdateIn(BaseModel):
    role: str
