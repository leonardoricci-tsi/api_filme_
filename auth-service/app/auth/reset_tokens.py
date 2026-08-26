import secrets
from datetime import timedelta

from sqlalchemy.orm import Session

from app.database import utc_now_naive
from app.models import ResetToken

RESET_TOKEN_EXPIRE_MINUTES = 30


def criar_reset_token(db: Session, usuario_id: int) -> ResetToken:
    """Gera um token aleatório e criptograficamente seguro (secrets.token_urlsafe,
    não um UUID sequencial nem previsível) e grava com expira_em = agora + 30min."""
    reset_token = ResetToken(
        token=secrets.token_urlsafe(32),
        usuario_id=usuario_id,
        expira_em=utc_now_naive() + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES),
    )
    db.add(reset_token)
    db.commit()
    return reset_token


def validar_reset_token(db: Session, token: str) -> ResetToken | None:
    """As 3 checagens da atividade: existe, não expirou, não foi usado.
    Qualquer uma falhando, devolve None — quem chama recusa a troca sem
    distinguir qual delas falhou, pra não vazar informação sobre o token."""
    reset_token = db.query(ResetToken).filter(ResetToken.token == token).first()
    if reset_token is None:
        return None
    if reset_token.usado:
        return None
    if reset_token.expira_em < utc_now_naive():
        return None
    return reset_token


def marcar_usado(db: Session, reset_token: ResetToken) -> None:
    reset_token.usado = True
    db.commit()
