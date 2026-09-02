from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.security import decode_access_token
from app.database import get_db
from app.models import Usuario

bearer_scheme = HTTPBearer(auto_error=False)


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

    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise credenciais_invalidas
    return usuario


def require_admin(usuario_atual: Usuario = Depends(get_current_user)) -> Usuario:
    if usuario_atual.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso restrito a admins")
    return usuario_atual
