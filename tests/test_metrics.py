from prometheus_client import REGISTRY

from tests.conftest import auth_headers, criar_token


def _amostra(nome: str, **labels) -> float:
    return REGISTRY.get_sample_value(nome, labels) or 0.0


def test_conta_requisicao_por_rota_template_e_status_exato(client, auth_service):
    """A rota entra como template (/profiles/{usuario_id}), não com o id —
    senão cada usuário viraria uma série nova no Prometheus. E o status é o
    exato (403), não agrupado em "4xx"."""
    labels = {"handler": "/profiles/{usuario_id}", "method": "PATCH", "status": "403"}
    antes = _amostra("http_requests_total", **labels)
    token = criar_token(usuario_id=901)

    for alvo in (902, 903):
        client.patch(f"/profiles/{alvo}", json={"bio": "x"}, headers=auth_headers(token))

    assert _amostra("http_requests_total", **labels) == antes + 2


def test_registra_latencia(client, auth_service):
    labels = {"handler": "/profiles/{usuario_id}", "method": "GET"}
    antes = _amostra("http_request_duration_seconds_count", **labels)

    client.get("/profiles/904", headers=auth_headers(criar_token(usuario_id=904)))

    assert _amostra("http_request_duration_seconds_count", **labels) == antes + 1
    assert _amostra("http_request_duration_seconds_sum", **labels) > 0


def test_health_fica_fora_das_metricas(client):
    """O HEALTHCHECK do Docker chama o /health a cada 15s: contar isso
    inflaria req/min com tráfego que não é de usuário."""
    client.get("/health/live")
    client.get("/health/live")

    nomes = {s.labels.get("handler") for m in REGISTRY.collect() for s in m.samples}
    assert "/health/live" not in nomes
    assert "/health" not in nomes
