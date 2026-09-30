from functools import lru_cache

import redis

from app.config import get_settings


@lru_cache
def get_redis() -> redis.Redis:
    """Dependência do FastAPI (não só um singleton solto): os testes trocam
    isso por um fakeredis via `app.dependency_overrides`, sem precisar de
    um Redis de verdade rodando."""
    settings = get_settings()
    # Timeouts curtos: com o Redis fora, o /health (e o POST /logs, que é
    # fire-and-forget do lado de quem chama) falha em ~2s em vez de ficar
    # pendurado esperando o timeout padrão do sistema.
    return redis.from_url(
        settings.redis_url, decode_responses=True, socket_connect_timeout=2, socket_timeout=2
    )
