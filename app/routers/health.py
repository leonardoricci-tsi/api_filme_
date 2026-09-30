import time
from collections.abc import Callable

import httpx
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.services import storage

router = APIRouter(tags=["health"])

# Serviços internos: pergunta só se estão VIVOS (/health/live), nunca o
# /health completo deles — senão uma queda do MySQL apareceria em cascata
# no health de todo mundo. A saúde das dependências de cada um é problema
# do /health dele.
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


def _servico_vivo(url_base: str) -> Callable[[], None]:
    def checar() -> None:
        httpx.get(f"{url_base}/health/live", timeout=_TIMEOUT_SERVICO).raise_for_status()

    return checar


@router.get("/health/live")
def liveness() -> dict:
    """Liveness: o processo está de pé e respondendo. Não testa nada além
    disso de propósito — se isso falhar, reiniciar o container resolve."""
    return {"status": "ok"}


@router.get(
    "/health",
    responses={503: {"description": "Dependência crítica fora (MySQL): não consigo atender"}},
)
def readiness(response: Response, db: Session = Depends(get_db)) -> dict:
    """Readiness: consigo atender de verdade? Testa cada dependência.

    Só o MySQL é crítico: sem ele, quase nenhuma rota funciona, então 503
    (o orquestrador para de mandar tráfego, mas não reinicia — reiniciar não
    faz o banco voltar). As outras deixam o serviço "degraded" com 200:
    sem o Garage só as fotos param; sem o log-service a auditoria é
    fire-and-forget; sem o auth-service, quem já tem token continua usando
    (JWT verificado localmente). Tirar o catálogo inteiro do ar por
    qualquer uma delas derrubaria também tudo o que ainda funciona."""
    settings = get_settings()
    checagens = {
        "mysql": _checar(lambda: db.execute(text("SELECT 1")), critica=True),
        "auth-service": _checar(_servico_vivo(settings.auth_service_url), critica=False),
        "log-service": _checar(_servico_vivo(settings.log_service_url), critica=False),
        "garage": _checar(storage.verificar_bucket, critica=False),
    }
    return _resumir(checagens, response)


def _resumir(checagens: dict, response: Response) -> dict:
    falhas = [c for c in checagens.values() if c["status"] != "ok"]
    if any(c["critica"] for c in falhas):
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        situacao = "fail"
    else:
        situacao = "degraded" if falhas else "ok"
    return {"status": situacao, "checagens": checagens}
