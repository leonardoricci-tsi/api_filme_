from datetime import datetime, timedelta, timezone

import httpx
import jwt

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


class PapelNaoAtualizado(Exception):
    """O auth-service não confirmou a troca de papel do plano pago."""


def definir_papel_pago(usuario_id: int, papel: str) -> None:
    """Pede ao auth-service (dono da tabela `usuarios`) pra trocar o papel
    de quem pagou ou cancelou um plano (atividade 7).

    Quem chama não é um usuário, é o próprio catálogo: o token é de
    SERVIÇO — assinado com o mesmo JWT_SECRET, com `servico` e sem `sub`,
    válido por 1 minuto. Não serve como token de usuário em lugar nenhum."""
    settings = get_settings()
    token = jwt.encode(
        {
            "servico": "catalogo",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=1),
        },
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    try:
        resposta = forward(
            "PUT",
            f"/internal/users/{usuario_id}/role",
            json={"role": papel},
            headers={"Authorization": f"Bearer {token}"},
        )
    except AuthServiceUnavailable as erro:
        raise PapelNaoAtualizado(str(erro)) from erro
    if resposta.status_code != 200:
        raise PapelNaoAtualizado(f"auth-service respondeu {resposta.status_code}")
