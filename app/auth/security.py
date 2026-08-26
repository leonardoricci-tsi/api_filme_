import jwt

from app.config import get_settings

settings = get_settings()


def decode_access_token(token: str) -> dict | None:
    """Verifica a assinatura e a expiração localmente — sem round-trip pro
    auth-service. É a vantagem de o JWT ser autocontido: o catálogo confia
    no que o token diz (sub, role) porque só quem tem JWT_SECRET consegue
    assiná-lo, e esse segredo é compartilhado só entre os dois serviços."""
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError:
        return None
