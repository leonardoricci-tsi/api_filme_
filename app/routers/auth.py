from fastapi import APIRouter, Body, Depends, Header, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials

from app.auth.dependencies import bearer_scheme
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


def _bearer_header(credentials: HTTPAuthorizationCredentials | None) -> dict:
    return {"Authorization": f"Bearer {credentials.credentials}"} if credentials else {}


@router.get("/admin/users")
def listar_usuarios(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> JSONResponse:
    """Proxy pro auth-service — só ele tem a tabela `usuarios`, então quem
    decide se o chamador é admin (403 se não for) é o auth-service, não o
    catálogo (`auth-service/app/routers/admin.py`).

    Usa `Depends(bearer_scheme)` (não `Header(None)` cru) só pra registrar
    esse endpoint como protegido no OpenAPI — assim o botão "Authorize" do
    Swagger funciona aqui também, igual no resto da API."""
    try:
        resposta = forward("GET", "/auth/admin/users", headers=_bearer_header(credentials))
    except AuthServiceUnavailable as erro:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(erro)) from erro
    return _proxy(resposta)


@router.patch("/admin/users/{usuario_id}/role")
def alterar_papel_usuario(
    usuario_id: int,
    dados: dict = Body(...),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> JSONResponse:
    try:
        resposta = forward(
            "PATCH",
            f"/auth/admin/users/{usuario_id}/role",
            json=dados,
            headers=_bearer_header(credentials),
        )
    except AuthServiceUnavailable as erro:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(erro)) from erro
    return _proxy(resposta)
