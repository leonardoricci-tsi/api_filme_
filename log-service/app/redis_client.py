from functools import lru_cache

import redis

from app.config import get_settings


@lru_cache
def get_redis() -> redis.Redis:
    """Dependência do FastAPI (não só um singleton solto): os testes trocam
    isso por um fakeredis via `app.dependency_overrides`, sem precisar de
    um Redis de verdade rodando."""
    settings = get_settings()
    return redis.from_url(settings.redis_url, decode_responses=True)
