import httpx

from app.config import get_settings

_http_client: httpx.Client | None = None


class AuthServiceUnavailable(Exception):
    """O auth-service não respondeu (fora do ar, rede interna com problema)."""


def _get_http_client() -> httpx.Client:
    global _http_client
    if _http_client is None:
        settings = get_settings()
        _http_client = httpx.Client(base_url=settings.auth_service_url, timeout=10.0)
    return _http_client


def forward(method: str, path: str, **kwargs) -> httpx.Response:
    """Repassa a requisição pro auth-service, na rede interna do Docker.

    O catálogo é o único ponto de entrada público — toda chamada relacionada
    a usuário (registro, login, perfil, esqueci-senha) entra por aqui e
    atravessa a rede interna até o auth-service, que nunca fica acessível
    de fora.
    """
    client = _get_http_client()
    try:
        return client.request(method, path, **kwargs)
    except httpx.RequestError as erro:
        raise AuthServiceUnavailable(
            "Serviço de autenticação indisponível no momento"
        ) from erro
