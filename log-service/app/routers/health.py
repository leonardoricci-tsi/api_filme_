import time

from fastapi import APIRouter, Depends, Response, status
from redis import Redis

from app.redis_client import get_redis

router = APIRouter(tags=["health"])


@router.get("/health/live")
def liveness() -> dict:
    """Liveness: o processo está de pé e respondendo — nada além disso."""
    return {"status": "ok"}


@router.get(
    "/health",
    responses={503: {"description": "Redis fora: não consigo gravar nem ler o log"}},
)
def readiness(response: Response, redis_client: Redis = Depends(get_redis)) -> dict:
    """Readiness: o Redis é a única dependência e é crítica — sem ele não
    existe log de auditoria (nem gravar, nem consultar), então 503. É esse
    503 que o HEALTHCHECK do Docker enxerga pra marcar o container como
    unhealthy quando o Redis cai."""
    inicio = time.perf_counter()
    try:
        redis_client.ping()
        redis = {"status": "ok"}
    except Exception as erro:  # noqa: BLE001 — qualquer falha do Redis vira "fail"
        redis = {"status": "fail", "erro": type(erro).__name__}
    redis["critica"] = True
    redis["ms"] = round((time.perf_counter() - inicio) * 1000)

    if redis["status"] != "ok":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {"status": redis["status"], "checagens": {"redis": redis}}
