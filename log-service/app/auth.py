import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import get_settings

settings = get_settings()
bearer_scheme = HTTPBearer(auto_error=False)


def require_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> None:
    """Decodifica o JWT localmente (mesmo JWT_SECRET do catálogo e do
    auth-service) e exige role=admin — mesmo princípio que o catálogo já usa
    pra verificar o token sem round-trip pro auth-service a cada request.
    Quem chama essa rota é sempre o catálogo, repassando o header
    Authorization original do usuário (não um token próprio de serviço)."""
    credenciais_invalidas = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas ou expiradas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise credenciais_invalidas

    try:
        payload = jwt.decode(
            credentials.credentials, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
    except jwt.PyJWTError as erro:
        raise credenciais_invalidas from erro

    if payload.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso restrito a admins")
