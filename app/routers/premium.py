from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.dependencies import UsuarioAutenticado, get_current_user
from app.database import get_db
from app.models import Assinatura
from app.openapi_responses import RESP_401, RESP_409_JA_PREMIUM, RESP_ERROS_PAGAMENTO
from app.services import log_client, pagamentos

router = APIRouter(prefix="/premium", tags=["premium"])


class CheckoutOut(BaseModel):
    checkout_url: str


class StatusPremiumOut(BaseModel):
    premium: bool


def eh_premium(db: Session, usuario_id: int) -> bool:
    assinatura = db.get(Assinatura, usuario_id)
    return assinatura is not None and assinatura.premium


@router.post(
    "/checkout",
    response_model=CheckoutOut,
    responses=RESP_401 | RESP_409_JA_PREMIUM | RESP_ERROS_PAGAMENTO,
)
def criar_checkout(
    request: Request,
    usuario_atual: UsuarioAutenticado = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CheckoutOut:
    """Abre o pagamento do plano premium no Stripe e devolve a URL dele.

    Devolve a URL em vez de um 302 porque o front é uma SPA que se
    autentica por header (Bearer), não por cookie: um redirect do servidor
    não levaria o token. O front recebe a URL e faz o redirecionamento.

    Qualquer papel pode assinar — premium é independente do papel (RBAC)."""
    if eh_premium(db, usuario_atual.id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Você já é premium")
    try:
        url = pagamentos.criar_checkout(usuario_atual.id)
    except pagamentos.PagamentoNaoConfigurado as erro:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(erro)) from erro
    except pagamentos.PagamentoIndisponivel as erro:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(erro)) from erro
    log_client.registrar_evento(
        usuario_atual.id,
        "abrir_checkout_premium",
        ip=request.client.host if request.client else None,
    )
    return CheckoutOut(checkout_url=url)


@router.get("/status", response_model=StatusPremiumOut, responses=RESP_401)
def status_premium(
    usuario_atual: UsuarioAutenticado = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StatusPremiumOut:
    """O front consulta isso na volta do checkout: a confirmação do
    pagamento chega por outro caminho (webhook), e pode chegar depois do
    navegador voltar — então ele pergunta até virar `true`."""
    return StatusPremiumOut(premium=eh_premium(db, usuario_atual.id))
