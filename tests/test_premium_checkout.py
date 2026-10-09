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
    monkeypatch.setattr(settings, "stripe_price_nerd", "price_nerd_fake")
    monkeypatch.setattr(settings, "stripe_price_stalker", "price_stalker_fake")
    falso = StripeFalso()
    monkeypatch.setattr(pagamentos, "_client", falso)
    return falso


def checkout(client, token, plano):
    return client.post("/premium/checkout", json={"plano": plano}, headers=auth_headers(token))


def test_cinefilo_compra_nerd_com_o_preco_e_o_usuario_certos(client, auth_service, stripe_configurado):
    resposta = checkout(client, criar_token(usuario_id=77, role="cinefilo"), "nerd")

    assert resposta.status_code == 200, resposta.text
    assert resposta.json() == {"checkout_url": "https://checkout.stripe.com/c/pay/cs_test_123"}
    params = stripe_configurado.params
    assert params["mode"] == "subscription"
    assert params["line_items"] == [{"price": "price_nerd_fake", "quantity": 1}]
    # É isso que o webhook usa pra saber quem pagou e qual plano.
    assert params["client_reference_id"] == "77"
    assert params["metadata"] == {"usuario_id": "77", "plano": "nerd"}
    assert params["subscription_data"]["metadata"] == {"usuario_id": "77", "plano": "nerd"}


def test_nerd_pode_subir_pra_stalker(client, auth_service, stripe_configurado):
    resposta = checkout(client, criar_token(role="nerd"), "stalker_do_tomhanks")

    assert resposta.status_code == 200
    assert stripe_configurado.params["line_items"][0]["price"] == "price_stalker_fake"


@pytest.mark.parametrize(
    ("papel", "plano"),
    [
        ("nerd", "nerd"),
        ("stalker_do_tomhanks", "nerd"),
        ("stalker_do_tomhanks", "stalker_do_tomhanks"),
        ("admin", "stalker_do_tomhanks"),
    ],
)
def test_nao_vende_plano_igual_ou_abaixo_do_papel_atual(client, stripe_configurado, papel, plano):
    resposta = checkout(client, criar_token(role=papel), plano)

    assert resposta.status_code == 409
    assert stripe_configurado.params is None


def test_cinefilo_nao_e_vendido_e_plano_inexistente_e_recusado(client, stripe_configurado):
    token = criar_token(role="cinefilo")

    assert checkout(client, token, "cinefilo").status_code == 422
    assert checkout(client, token, "admin").status_code == 422


def test_checkout_exige_login(client):
    assert client.post("/premium/checkout", json={"plano": "nerd"}).status_code == 401


def test_sem_chaves_do_stripe_checkout_responde_503(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "stripe_secret_key", "")

    assert checkout(client, criar_token(role="cinefilo"), "nerd").status_code == 503


def test_stripe_fora_do_ar_vira_502(client, stripe_configurado):
    stripe_configurado.erro = stripe.APIConnectionError("sem rede")

    assert checkout(client, criar_token(role="cinefilo"), "nerd").status_code == 502


def test_status_do_plano(client, db_session):
    db_session.add(Assinatura(usuario_id=79, premium=True, plano="nerd"))
    db_session.commit()

    assert client.get("/premium/status", headers=auth_headers(criar_token(usuario_id=79))).json() == {
        "premium": True,
        "plano": "nerd",
    }
    # Sem linha em `assinaturas` = plano gratuito.
    assert client.get("/premium/status", headers=auth_headers(criar_token(usuario_id=80))).json() == {
        "premium": False,
        "plano": None,
    }


def test_perfil_mostra_o_plano_pago(client, db_session, auth_service):
    db_session.add(Assinatura(usuario_id=64, premium=True, plano="stalker_do_tomhanks"))
    db_session.commit()
    quem_ve = auth_headers(criar_token(usuario_id=65))

    assert client.get("/profiles/64", headers=quem_ve).json()["plano"] == "stalker_do_tomhanks"
    assert client.get("/profiles/65", headers=quem_ve).json()["plano"] is None
