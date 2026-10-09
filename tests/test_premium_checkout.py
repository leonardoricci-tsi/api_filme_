from types import SimpleNamespace

import pytest
import stripe

from app.config import get_settings
from app.models import Assinatura
from app.services import pagamentos
from tests.conftest import auth_headers, criar_token


class StripeFalso:
    """Faz o papel do StripeClient: guarda o que o catálogo pediu e devolve
    uma sessão com URL — nenhuma chamada sai pra rede."""

    def __init__(self, erro: Exception | None = None):
        self.params = None
        self.erro = erro
        self.v1 = SimpleNamespace(checkout=SimpleNamespace(sessions=self))

    def create(self, params):
        if self.erro:
            raise self.erro
        self.params = params
        return SimpleNamespace(url="https://checkout.stripe.com/c/pay/cs_test_123")


@pytest.fixture()
def stripe_configurado(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "stripe_secret_key", "sk_test_fake")
    monkeypatch.setattr(settings, "stripe_price_id", "price_fake")
    falso = StripeFalso()
    monkeypatch.setattr(pagamentos, "_client", falso)
    return falso


def test_checkout_devolve_url_do_stripe_com_usuario_do_jwt(client, auth_service, stripe_configurado):
    resposta = client.post("/premium/checkout", headers=auth_headers(criar_token(usuario_id=77)))

    assert resposta.status_code == 200, resposta.text
    assert resposta.json() == {"checkout_url": "https://checkout.stripe.com/c/pay/cs_test_123"}
    params = stripe_configurado.params
    assert params["mode"] == "subscription"
    assert params["line_items"] == [{"price": "price_fake", "quantity": 1}]
    # É isso que o webhook usa pra saber quem pagou.
    assert params["client_reference_id"] == "77"
    assert params["subscription_data"]["metadata"] == {"usuario_id": "77"}


def test_checkout_exige_login(client):
    assert client.post("/premium/checkout").status_code == 401


def test_quem_ja_e_premium_nao_abre_outro_checkout(client, db_session, stripe_configurado):
    db_session.add(Assinatura(usuario_id=78, premium=True))
    db_session.commit()

    resposta = client.post("/premium/checkout", headers=auth_headers(criar_token(usuario_id=78)))

    assert resposta.status_code == 409
    assert stripe_configurado.params is None


def test_sem_chaves_do_stripe_checkout_responde_503(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "stripe_secret_key", "")

    resposta = client.post("/premium/checkout", headers=auth_headers(criar_token()))

    assert resposta.status_code == 503


def test_stripe_fora_do_ar_vira_502(client, stripe_configurado):
    stripe_configurado.erro = stripe.APIConnectionError("sem rede")

    resposta = client.post("/premium/checkout", headers=auth_headers(criar_token()))

    assert resposta.status_code == 502


def test_status_premium(client, db_session):
    db_session.add(Assinatura(usuario_id=79, premium=True))
    db_session.commit()

    assert client.get("/premium/status", headers=auth_headers(criar_token(usuario_id=79))).json() == {
        "premium": True
    }
    # Sem linha em `assinaturas` = usuário comum.
    assert client.get("/premium/status", headers=auth_headers(criar_token(usuario_id=80))).json() == {
        "premium": False
    }
