from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.security import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass
class UsuarioAutenticado:
    """Identidade extraída do JWT — o catálogo não tem mais a tabela
    `usuarios` (ela é do auth-service agora), então não há um model
    SQLAlchemy aqui: só o que o token já carrega."""

    id: int
    role: str
    nome: str


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> UsuarioAutenticado:
    credenciais_invalidas = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas ou expiradas",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise credenciais_invalidas

    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise credenciais_invalidas

    try:
        usuario_id = int(payload["sub"])
        role = payload["role"]
    except (KeyError, ValueError, TypeError) as erro:
        raise credenciais_invalidas from erro

    # .get com fallback: tokens emitidos antes do claim `nome` existir ainda
    # circulam até expirar (JWT_EXPIRE_MINUTES) — não podem virar 401 por isso.
    nome = payload.get("nome") or ""

    return UsuarioAutenticado(id=usuario_id, role=role, nome=nome)


def require_admin(
    usuario_atual: UsuarioAutenticado = Depends(get_current_user),
) -> UsuarioAutenticado:
    if usuario_atual.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso restrito a admins")
    return usuario_atual
