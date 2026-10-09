import json

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.dependencies import UsuarioAutenticado, get_current_user
from app.database import get_db
from app.models import Assinatura
from app.openapi_responses import (
    RESP_401,
    RESP_409_JA_PREMIUM,
    RESP_ERROS_PAGAMENTO,
    RESP_ERROS_WEBHOOK,
)
from app.services import log_client, pagamentos

router = APIRouter(prefix="/premium", tags=["premium"])

# O benefício do plano (atividade 7): quem não é premium guarda no máximo
# isso de favoritos; premium é ilimitado (routers/favorites.py).
LIMITE_FAVORITOS_GRATIS = 5


class CheckoutOut(BaseModel):
    checkout_url: str


class StatusPremiumOut(BaseModel):
    premium: bool
    # None = ilimitado (premium).
    limite_favoritos: int | None


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
    premium = eh_premium(db, usuario_atual.id)
    return StatusPremiumOut(
        premium=premium, limite_favoritos=None if premium else LIMITE_FAVORITOS_GRATIS
    )


def _ativar_premium(db: Session, sessao: dict) -> None:
    """checkout.session.completed: o pagamento foi concluído. Quem pagou
    vem do `client_reference_id` que o próprio catálogo pôs na sessão
    (o id do JWT na hora do checkout) — devolvido intacto pelo Stripe."""
    if sessao.get("mode") != "subscription" or not sessao.get("client_reference_id"):
        return
    usuario_id = int(sessao["client_reference_id"])
    assinatura = db.get(Assinatura, usuario_id)
    if assinatura is None:
        assinatura = Assinatura(usuario_id=usuario_id)
        db.add(assinatura)
    # Idempotente: o Stripe reenvia o mesmo evento se não receber 2xx a
    # tempo — processar duas vezes dá no mesmo resultado.
    assinatura.premium = True
    assinatura.stripe_customer_id = sessao.get("customer")
    assinatura.stripe_subscription_id = sessao.get("subscription")
    db.commit()
    log_client.registrar_evento(usuario_id, "premium_ativado")


def _desativar_premium(db: Session, assinatura_stripe: dict) -> None:
    """customer.subscription.deleted: a assinatura acabou (cancelada no
    painel do Stripe, ou cobrança recusada até esgotar as tentativas)."""
    assinatura = (
        db.query(Assinatura)
        .filter(Assinatura.stripe_subscription_id == assinatura_stripe.get("id"))
        .first()
    )
    if assinatura is None:
        return
    assinatura.premium = False
    db.commit()
    log_client.registrar_evento(assinatura.usuario_id, "premium_cancelado")


_TRATADORES = {
    "checkout.session.completed": _ativar_premium,
    "customer.subscription.deleted": _desativar_premium,
}


@router.post("/webhook", responses=RESP_ERROS_WEBHOOK)
async def receber_webhook(
    request: Request,
    stripe_signature: str | None = Header(None, alias="Stripe-Signature"),
    db: Session = Depends(get_db),
) -> dict:
    """Chamado PELO STRIPE, não pelo front — sem JWT: quem prova que a
    chamada é legítima é a assinatura no cabeçalho `Stripe-Signature`.

    Chega de forma assíncrona: pode vir antes ou depois do navegador
    voltar do checkout, e é a ÚNICA coisa que marca alguém como premium.

    `async` só pra ler o corpo bruto (`await request.body()`) — a
    assinatura é calculada sobre os bytes exatos que o Stripe mandou; se o
    FastAPI parseasse e re-serializasse o JSON, ela não bateria mais."""
    payload = await request.body()
    try:
        pagamentos.validar_webhook(payload, stripe_signature)
    except pagamentos.PagamentoNaoConfigurado as erro:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(erro)) from erro
    except pagamentos.AssinaturaWebhookInvalida as erro:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(erro)) from erro

    evento = json.loads(payload)
    tratador = _TRATADORES.get(evento.get("type"))
    # Evento que não interessa: 200 mesmo assim — erro faria o Stripe
    # ficar reenviando à toa.
    if tratador is not None:
        # Banco e log-service são síncronos: roda fora do event loop.
        await run_in_threadpool(tratador, db, evento["data"]["object"])
    return {"recebido": True}
