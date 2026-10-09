from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.config import get_settings

settings = get_settings()


def hash_password(senha: str) -> str:
    return bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(senha: str, senha_hash: str) -> bool:
    return bcrypt.checkpw(senha.encode("utf-8"), senha_hash.encode("utf-8"))


def create_access_token(usuario_id: int, role: str, nome: str) -> str:
    """O token carrega role e nome como claims — o catálogo lê os dois
    direto do JWT (localmente, sem round-trip de rede): role pra decidir o
    que autorizar, nome pra exibir de quem é cada comentário."""
    expira_em = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": str(usuario_id), "role": role, "nome": nome, "exp": expira_em}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> int | None:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError:
        return None
    sub = payload.get("sub")
    if sub is None:
        return None
    try:
        return int(sub)
    except ValueError:
        return None


def decode_service_token(token: str) -> dict | None:
    """Token de SERVIÇO (atividade 7): é o catálogo, não um usuário, pedindo
    pra trocar o papel de alguém depois de um pagamento confirmado. Mesmo
    JWT_SECRET compartilhado, mas outro formato: tem `servico` e NÃO tem
    `sub` — então não serve como token de usuário (decode_access_token
    exige `sub`), e token de usuário não serve aqui (não tem `servico`)."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError:
        return None
    if payload.get("servico") != "catalogo" or "sub" in payload:
        return None
    return payload
