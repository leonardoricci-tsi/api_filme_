import httpx
import respx
from httpx import Response

from app.config import get_settings
from app.routers import storage_proxy


def _garage_url() -> str:
    return get_settings().s3_endpoint_url


def test_repassa_caminho_query_e_host_assinado_sem_alterar(client, monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "s3_public_url", "https://catalogo.exemplo.com")
    monkeypatch.setattr(storage_proxy, "_http_client", None)
    query = "X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=GK1%2F20260929%2Fgarage%2Fs3%2Faws4_request&X-Amz-Signature=abc"

    with respx.mock:
        rota = respx.get(url__startswith=f"{_garage_url()}/{settings.s3_bucket}/perfis/7/a.png").mock(
            return_value=Response(200, content=b"\x89PNG...", headers={"content-type": "image/png"})
        )

        resposta = client.get(f"/{settings.s3_bucket}/perfis/7/a.png?{query}")

    assert resposta.status_code == 200
    assert resposta.content == b"\x89PNG..."
    assert resposta.headers["content-type"] == "image/png"
    enviado = rota.calls.last.request
    # O Host tem que ser o que entrou na assinatura, não o nome interno do Garage.
    assert enviado.headers["host"] == "catalogo.exemplo.com"
    # Query byte a byte: o %2F continua %2F, nada foi recodificado.
    assert enviado.url.query.decode() == query


def test_403_do_garage_volta_pro_navegador(client, monkeypatch):
    """Assinatura inválida/expirada é o Garage que recusa — o catálogo não
    decide nada, só devolve a recusa."""
    monkeypatch.setattr(storage_proxy, "_http_client", None)
    bucket = get_settings().s3_bucket

    with respx.mock:
        respx.get(url__startswith=f"{_garage_url()}/{bucket}/").mock(
            return_value=Response(403, content=b"<Error><Code>AccessDenied</Code></Error>")
        )

        resposta = client.get(f"/{bucket}/perfis/7/a.png")

    assert resposta.status_code == 403


def test_garage_fora_do_ar_da_502(client, monkeypatch):
    monkeypatch.setattr(storage_proxy, "_http_client", None)
    bucket = get_settings().s3_bucket

    with respx.mock:
        respx.get(url__startswith=f"{_garage_url()}/{bucket}/").mock(
            side_effect=httpx.ConnectError("sem rota")
        )

        resposta = client.get(f"/{bucket}/perfis/7/a.png?X-Amz-Signature=abc")

    assert resposta.status_code == 502


def test_so_o_caminho_do_bucket_vai_pro_garage(client):
    """Qualquer outro caminho continua sendo do app (API ou Angular)."""
    with respx.mock:  # nenhuma rota mockada: se tentasse o Garage, estouraria
        resposta = client.get("/openapi.json")

    assert resposta.status_code == 200
