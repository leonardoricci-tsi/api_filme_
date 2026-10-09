import stripe

from app.config import get_settings

_client: stripe.StripeClient | None = None


class PagamentoNaoConfigurado(Exception):
    """STRIPE_SECRET_KEY/STRIPE_PRICE_ID vazios — premium desligado neste ambiente."""


class PagamentoIndisponivel(Exception):
    """O Stripe não respondeu ou recusou a chamada."""


def _get_client() -> stripe.StripeClient:
    global _client
    settings = get_settings()
    if not settings.stripe_secret_key or not settings.stripe_price_id:
        raise PagamentoNaoConfigurado("Plano premium indisponível neste ambiente")
    # Chave de teste (sk_test_...) sempre: a atividade inteira roda no modo
    # de teste do Stripe, nenhuma cobrança real.
    if _client is None:
        _client = stripe.StripeClient(settings.stripe_secret_key)
    return _client


def criar_checkout(usuario_id: int) -> str:
    """Cria a Checkout Session da assinatura premium e devolve a URL da
    página de pagamento — hospedada pelo Stripe, é lá (e não aqui) que o
    cartão é digitado.

    `client_reference_id` é o que liga o pagamento ao usuário: o Stripe
    devolve esse valor intacto no webhook. Vem do JWT de quem chamou,
    nunca do corpo da requisição."""
    settings = get_settings()
    client = _get_client()
    try:
        sessao = client.v1.checkout.sessions.create(
            params={
                "mode": "subscription",
                "line_items": [{"price": settings.stripe_price_id, "quantity": 1}],
                "client_reference_id": str(usuario_id),
                # Também na assinatura: o evento de cancelamento
                # (customer.subscription.deleted) não traz a sessão, só ela.
                "subscription_data": {"metadata": {"usuario_id": str(usuario_id)}},
                "success_url": f"{settings.catalog_public_url}/app/premium?checkout=sucesso",
                "cancel_url": f"{settings.catalog_public_url}/app/premium?checkout=cancelado",
            }
        )
    except stripe.StripeError as erro:
        raise PagamentoIndisponivel("Provedor de pagamento indisponível no momento") from erro
    return sessao.url
