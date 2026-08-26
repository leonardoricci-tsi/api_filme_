from pydantic import BaseModel, EmailStr, Field


class RegisterIn(BaseModel):
    nome: str = Field(min_length=1, max_length=255)
    email: EmailStr
    senha: str = Field(min_length=8, max_length=72)


class LoginIn(BaseModel):
    email: EmailStr
    senha: str
