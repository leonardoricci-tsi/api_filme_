from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.reset_tokens import criar_reset_token, marcar_usado, validar_reset_token
from app.auth.security import hash_password
from app.config import get_settings
from app.database import get_db
from app.models import Usuario
from app.schemas.password_reset import ForgotPasswordIn, ResetPasswordIn
from app.services.mailer import send_reset_email

router = APIRouter(prefix="/auth", tags=["password-reset"])

MENSAGEM_GENERICA = "Se esse email estiver cadastrado, você vai receber um link de redefinição."

_RESP_LINK_INVALIDO = {
    400: {
        "description": "Token inexistente, expirado ou já usado",
        "content": {
            "application/json": {"example": {"detail": "Link inválido, expirado ou já utilizado"}}
        },
    }
}


@router.post("/forgot-password")
def forgot_password(dados: ForgotPasswordIn, db: Session = Depends(get_db)) -> dict:
    usuario = db.query(Usuario).filter(Usuario.email == dados.email).first()
    if usuario is not None:
        reset_token = criar_reset_token(db, usuario.id)
        settings = get_settings()
        link = f"{settings.catalog_public_url}/redefinir-senha?token={reset_token.token}"
        send_reset_email(usuario.email, link)
    # Mesma resposta exista ou não o email — não dá pra descobrir quem tem
    # conta tentando um e-mail de cada vez.
    return {"detail": MENSAGEM_GENERICA}


@router.post("/reset-password", responses=_RESP_LINK_INVALIDO)
def reset_password(dados: ResetPasswordIn, db: Session = Depends(get_db)) -> dict:
    reset_token = validar_reset_token(db, dados.token)
    if reset_token is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Link inválido, expirado ou já utilizado",
        )

    usuario = db.get(Usuario, reset_token.usuario_id)
    usuario.senha_hash = hash_password(dados.nova_senha)
    marcar_usado(db, reset_token)  # já dá commit, junto com a troca de senha acima

    return {"detail": "Senha redefinida com sucesso"}
