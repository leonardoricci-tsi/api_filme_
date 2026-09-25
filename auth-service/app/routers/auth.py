from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.security import create_access_token, hash_password, verify_password
from app.database import get_db
from app.models import Usuario
from app.openapi_responses import RESP_401
from app.schemas.auth import LoginIn, RegisterIn, TokenOut, UsuarioOut
from app.services import log_client

router = APIRouter(prefix="/auth", tags=["auth"])

_RESP_EMAIL_DUPLICADO = {
    400: {
        "description": "E-mail já cadastrado",
        "content": {"application/json": {"example": {"detail": "Email já cadastrado"}}},
    }
}
_RESP_LOGIN_INVALIDO = {
    401: {
        "description": "E-mail ou senha não batem com nenhum usuário cadastrado",
        "content": {"application/json": {"example": {"detail": "Email ou senha inválidos"}}},
    }
}


@router.post(
    "/register",
    response_model=TokenOut,
    status_code=status.HTTP_201_CREATED,
    responses=_RESP_EMAIL_DUPLICADO,
)
def register(dados: RegisterIn, db: Session = Depends(get_db)) -> TokenOut:
    email_em_uso = db.query(Usuario).filter(Usuario.email == dados.email).first()
    if email_em_uso is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email já cadastrado")

    usuario = Usuario(
        nome=dados.nome,
        email=dados.email,
        senha_hash=hash_password(dados.senha),
        role="cinefilo",
    )
    db.add(usuario)
    db.commit()

    token = create_access_token(usuario.id, usuario.role, usuario.nome)
    return TokenOut(access_token=token)


@router.post("/login", response_model=TokenOut, responses=_RESP_LOGIN_INVALIDO)
def login(dados: LoginIn, request: Request, db: Session = Depends(get_db)) -> TokenOut:
    credenciais_invalidas = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Email ou senha inválidos"
    )

    usuario = db.query(Usuario).filter(Usuario.email == dados.email).first()
    if usuario is None or not verify_password(dados.senha, usuario.senha_hash):
        raise credenciais_invalidas

    token = create_access_token(usuario.id, usuario.role, usuario.nome)
    # Evento mínimo exigido pela atividade 5 — login é decidido aqui (é
    # quem tem a tabela `usuarios`), não no catálogo, que só repassa.
    log_client.registrar_evento(
        usuario.id, "login", ip=request.client.host if request.client else None
    )
    return TokenOut(access_token=token)


@router.get("/me", response_model=UsuarioOut, responses=RESP_401)
def me(usuario_atual: Usuario = Depends(get_current_user)) -> UsuarioOut:
    return usuario_atual
