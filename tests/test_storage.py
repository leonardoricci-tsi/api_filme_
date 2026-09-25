from urllib.parse import parse_qs, urlparse

import pytest
from botocore.stub import Stubber

from app.config import get_settings
from app.services import storage


@pytest.fixture(autouse=True)
def _clients_limpos(monkeypatch):
    # Os clients são cacheados no módulo — cada teste começa do zero, com
    # credenciais falsas (nenhum teste aqui fala com um Garage de verdade).
    monkeypatch.setattr(storage, "_client_interno", None)
    monkeypatch.setattr(storage, "_client_publico", None)
    settings = get_settings()
    monkeypatch.setattr(settings, "s3_access_key", "GK" + "0" * 32)
    monkeypatch.setattr(settings, "s3_secret_key", "f" * 64)
    monkeypatch.setattr(settings, "s3_endpoint_url", "http://garage:3900")
    monkeypatch.setattr(settings, "s3_public_url", "http://fotos.exemplo.com:3900")


def test_url_temporaria_usa_host_publico_e_expira():
    settings = get_settings()
    url = urlparse(storage.gerar_url_temporaria("perfis/1/abc.jpg"))
    query = parse_qs(url.query)

    # Assinada pro host que o navegador abre, não pro nome interno do Docker.
    assert url.netloc == "fotos.exemplo.com:3900"
    # Path-style: /bucket/chave.
    assert url.path == f"/{settings.s3_bucket}/perfis/1/abc.jpg"
    assert query["X-Amz-Expires"] == [str(settings.s3_url_expira_segundos)]
    # Região entra na assinatura — tem que ser a do garage.toml.
    assert f"/{settings.s3_region}/s3/aws4_request" in query["X-Amz-Credential"][0]


def test_enviar_objeto_grava_no_bucket_pela_rede_interna():
    settings = get_settings()
    client = storage._get_client_interno()
    assert client.meta.endpoint_url == "http://garage:3900"

    with Stubber(client) as stub:
        stub.add_response(
            "put_object",
            {},
            {
                "Bucket": settings.s3_bucket,
                "Key": "perfis/1/abc.png",
                "Body": b"conteudo",
                "ContentType": "image/png",
            },
        )
        storage.enviar_objeto("perfis/1/abc.png", b"conteudo", "image/png")
        stub.assert_no_pending_responses()


def test_enviar_objeto_falha_vira_storage_unavailable():
    with Stubber(storage._get_client_interno()) as stub:
        stub.add_client_error("put_object", service_error_code="InternalError")
        with pytest.raises(storage.StorageUnavailable):
            storage.enviar_objeto("perfis/1/abc.png", b"conteudo", "image/png")


def test_apagar_objeto_engole_erro():
    with Stubber(storage._get_client_interno()) as stub:
        stub.add_client_error("delete_object", service_error_code="InternalError")
        storage.apagar_objeto("perfis/1/antiga.png")  # não levanta
