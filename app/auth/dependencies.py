import time

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.security import decode_access_token
from app.database import get_db
from app.models import Usuario

bearer_scheme = HTTPBearer(auto_error=False)

# Cache curto do usuário autenticado: evita bater no MySQL remoto (round-trip
# caro) em toda requisição só pra confirmar que o usuário do token ainda
# existe. TTL curto o suficiente pra não importar em termos de segurança —
# o próprio token já expira e pode ser revogado só trocando JWT_SECRET.
_usuario_cache: dict[int, tuple[Usuario, float]] = {}
USUARIO_CACHE_TTL_SECONDS = 30


def clear_usuario_cache() -> None:
    """Usado pelos testes pra evitar vazamento de cache entre bancos diferentes."""
    _usuario_cache.clear()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    credenciais_invalidas = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas ou expiradas",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise credenciais_invalidas

    usuario_id = decode_access_token(credentials.credentials)
    if usuario_id is None:
        raise credenciais_invalidas

    agora = time.monotonic()
    em_cache = _usuario_cache.get(usuario_id)
    if em_cache is not None and agora < em_cache[1]:
        return em_cache[0]

    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        _usuario_cache.pop(usuario_id, None)
        raise credenciais_invalidas

    _usuario_cache[usuario_id] = (usuario, agora + USUARIO_CACHE_TTL_SECONDS)
    return usuario
