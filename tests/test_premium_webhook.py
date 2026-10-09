import hashlib
import hmac
import json
import time

import pytest

from app.config import get_settings
from app.models import Assinatura

SEGREDO = "whsec_teste_fake"


@pytest.fixture(autouse=True)
def webhook_configurado(monkeypatch):
    monkeypatch.setattr(get_settings(), "stripe_webhook_secret", SEGREDO)


def assinar(corpo: bytes, segredo: str = SEGREDO, timestamp: int | None = None) -> str:
    """Monta o cabeçalho Stripe-Signature do jeito que o Stripe monta:
    HMAC-SHA256 de "<timestamp>.<corpo>" com o segredo do endpoint."""
    timestamp = timestamp or int(time.time())
    mac = hmac.new(segredo.encode(), f"{timestamp}.".encode() + corpo, hashlib.sha256)
    return f"t={timestamp},v1={mac.hexdigest()}"


def evento_checkout(usuario_id: int = 42) -> bytes:
    return json.dumps(
        {
            "id": "evt_test_1",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "object": "checkout.session",
                    "mode": "subscription",
                    "client_reference_id": str(usuario_id),
                    "customer": "cus_test_1",
                    "subscription": "sub_test_1",
                    "payment_status": "paid",
                }
            },
        }
    ).encode()


def enviar(client, corpo: bytes, assinatura: str | None):
    headers = {"Content-Type": "application/json"}
    if assinatura is not None:
        headers["Stripe-Signature"] = assinatura
    return client.post("/premium/webhook", content=corpo, headers=headers)


def test_checkout_concluido_marca_usuario_como_premium(client, db_session, auth_service):
    corpo = evento_checkout(usuario_id=42)

    resposta = enviar(client, corpo, assinar(corpo))

    assert resposta.status_code == 200, resposta.text
    assinatura = db_session.get(Assinatura, 42)
    assert assinatura.premium is True
    assert assinatura.stripe_customer_id == "cus_test_1"
    assert assinatura.stripe_subscription_id == "sub_test_1"


def test_mesmo_evento_duas_vezes_nao_quebra(client, db_session, auth_service):
    corpo = evento_checkout(usuario_id=43)

    assert enviar(client, corpo, assinar(corpo)).status_code == 200
    assert enviar(client, corpo, assinar(corpo)).status_code == 200

    assert db_session.query(Assinatura).filter_by(usuario_id=43).count() == 1


def test_sem_cabecalho_de_assinatura_e_recusado(client, db_session):
    resposta = enviar(client, evento_checkout(usuario_id=44), None)

    assert resposta.status_code == 400
    assert db_session.get(Assinatura, 44) is None


def test_assinado_com_outro_segredo_e_recusado(client, db_session):
    corpo = evento_checkout(usuario_id=45)

    resposta = enviar(client, corpo, assinar(corpo, segredo="whsec_de_um_atacante"))

    assert resposta.status_code == 400
    assert db_session.get(Assinatura, 45) is None


def test_corpo_alterado_depois_de_assinado_e_recusado(client, db_session):
    """Assinatura de um evento legítimo do usuário 46, corpo trocado pro 47."""
    assinatura = assinar(evento_checkout(usuario_id=46))

    resposta = enviar(client, evento_checkout(usuario_id=47), assinatura)

    assert resposta.status_code == 400
    assert db_session.get(Assinatura, 47) is None


def test_evento_velho_reenviado_e_recusado(client, db_session):
    corpo = evento_checkout(usuario_id=48)
    uma_hora_atras = int(time.time()) - 3600

    resposta = enviar(client, corpo, assinar(corpo, timestamp=uma_hora_atras))

    assert resposta.status_code == 400
    assert db_session.get(Assinatura, 48) is None


def test_sem_segredo_configurado_responde_503(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "stripe_webhook_secret", "")
    corpo = evento_checkout()

    assert enviar(client, corpo, assinar(corpo)).status_code == 503


def test_assinatura_cancelada_tira_o_premium(client, db_session, auth_service):
    db_session.add(Assinatura(usuario_id=49, premium=True, stripe_subscription_id="sub_test_49"))
    db_session.commit()
    corpo = json.dumps(
        {
            "type": "customer.subscription.deleted",
            "data": {"object": {"object": "subscription", "id": "sub_test_49"}},
        }
    ).encode()

    resposta = enviar(client, corpo, assinar(corpo))

    assert resposta.status_code == 200
    db_session.refresh(db_session.get(Assinatura, 49))
    assert db_session.get(Assinatura, 49).premium is False


def test_evento_que_nao_interessa_responde_200_sem_mexer_no_banco(client, db_session):
    corpo = json.dumps({"type": "invoice.paid", "data": {"object": {}}}).encode()

    assert enviar(client, corpo, assinar(corpo)).status_code == 200
    assert db_session.query(Assinatura).count() == 0
