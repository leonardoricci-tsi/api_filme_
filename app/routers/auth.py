from fastapi import APIRouter, Header, HTTPException, status
from fastapi.responses import JSONResponse

from app.schemas.auth import LoginIn, RegisterIn
from app.schemas.password_reset import ForgotPasswordIn, ResetPasswordIn
from app.services.auth_client import AuthServiceUnavailable, forward

router = APIRouter(prefix="/auth", tags=["auth"])


def _proxy(response) -> JSONResponse:
    return JSONResponse(status_code=response.status_code, content=response.json())


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(dados: RegisterIn) -> JSONResponse:
    try:
        resposta = forward("POST", "/auth/register", json=dados.model_dump())
    except AuthServiceUnavailable as erro:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(erro)) from erro
    return _proxy(resposta)


@router.post("/login")
def login(dados: LoginIn) -> JSONResponse:
    try:
        resposta = forward("POST", "/auth/login", json=dados.model_dump())
    except AuthServiceUnavailable as erro:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(erro)) from erro
    return _proxy(resposta)


@router.get("/me")
def me(authorization: str | None = Header(None)) -> JSONResponse:
    headers = {"Authorization": authorization} if authorization else {}
    try:
        resposta = forward("GET", "/auth/me", headers=headers)
    except AuthServiceUnavailable as erro:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(erro)) from erro
    return _proxy(resposta)


@router.post("/forgot-password")
def forgot_password(dados: ForgotPasswordIn) -> JSONResponse:
    try:
        resposta = forward("POST", "/auth/forgot-password", json=dados.model_dump())
    except AuthServiceUnavailable as erro:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(erro)) from erro
    return _proxy(resposta)


@router.post("/reset-password")
def reset_password(dados: ResetPasswordIn) -> JSONResponse:
    try:
        resposta = forward("POST", "/auth/reset-password", json=dados.model_dump())
    except AuthServiceUnavailable as erro:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(erro)) from erro
    return _proxy(resposta)
