import httpx

from app.config import get_settings

_http_client: httpx.Client | None = None


def _get_http_client() -> httpx.Client:
    global _http_client
    if _http_client is None:
        settings = get_settings()
        _http_client = httpx.Client(base_url=settings.log_service_url, timeout=5.0)
    return _http_client


def registrar_evento(usuario_id: int, acao: str, ip: str | None = None) -> None:
    """Dispara o evento de auditoria pro log-service (atividade 5).

    Fire-and-forget: uma falha aqui (log-service fora do ar, rede interna
    com problema) nunca pode derrubar o login de verdade — auditoria é
    observabilidade, não pode virar motivo de 500. Timeout curto e erro
    engolido de propósito."""
    try:
        _get_http_client().post(
            "/logs", json={"usuario_id": usuario_id, "acao": acao, "ip": ip}
        )
    except Exception:  # noqa: BLE001 — auditoria nunca pode derrubar o login real
        pass
