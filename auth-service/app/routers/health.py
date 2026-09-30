import time
from collections.abc import Callable

import httpx
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db

router = APIRouter(tags=["health"])

_TIMEOUT_SERVICO = 2.0


def _checar(funcao: Callable[[], None], critica: bool) -> dict:
    inicio = time.perf_counter()
    try:
        funcao()
        resultado = {"status": "ok"}
    except Exception as erro:  # noqa: BLE001 — qualquer falha da dependência vira "fail"
        resultado = {"status": "fail", "erro": type(erro).__name__}
    resultado["critica"] = critica
    resultado["ms"] = round((time.perf_counter() - inicio) * 1000)
    return resultado


@router.get("/health/live")
def liveness() -> dict:
    """Liveness: o processo está de pé e respondendo — nada além disso."""
    return {"status": "ok"}


@router.get(
    "/health",
    responses={503: {"description": "Dependência crítica fora (MySQL): não consigo atender"}},
)
def readiness(response: Response, db: Session = Depends(get_db)) -> dict:
    """Readiness: o MySQL (tabela `usuarios`) é crítico — sem ele não há
    login nem cadastro, então 503. O log-service não: a auditoria do login
    é fire-and-forget (atividade 5), o login funciona sem ela — só fica
    "degraded". Do log-service pergunta só se está vivo (/health/live),
    nunca o /health completo dele, pra não encadear falhas."""
    settings = get_settings()

    def log_service_vivo() -> None:
        httpx.get(f"{settings.log_service_url}/health/live", timeout=_TIMEOUT_SERVICO).raise_for_status()

    checagens = {
        "mysql": _checar(lambda: db.execute(text("SELECT 1")), critica=True),
        "log-service": _checar(log_service_vivo, critica=False),
    }
    falhas = [c for c in checagens.values() if c["status"] != "ok"]
    if any(c["critica"] for c in falhas):
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        situacao = "fail"
    else:
        situacao = "degraded" if falhas else "ok"
    return {"status": situacao, "checagens": checagens}
