from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, status
from redis import Redis

from app.auth import require_admin
from app.redis_client import get_redis
from app.schemas import LogEventIn, LogEventOut

router = APIRouter(tags=["logs"])

# Um Stream só, com todo evento de todo serviço — auditoria não precisa de
# um stream por serviço, precisa da linha do tempo inteira pra reconstruir
# "o que aconteceu aqui".
STREAM_KEY = "audit_log"


@router.post("/logs", status_code=status.HTTP_201_CREATED)
def registrar_evento(
    evento: LogEventIn,
    redis_client: Redis = Depends(get_redis),
) -> dict:
    """Sem autenticação própria: só alcançável de dentro da rede Docker
    (log-service não tem porta publicada pro host), chamado pelo catálogo e
    pelo auth-service depois que eles já identificaram o usuário — mesmo
    nível de confiança que o resto da comunicação interna entre serviços."""
    campos = {
        "usuario_id": str(evento.usuario_id),
        "acao": evento.acao,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ip": evento.ip or "",
    }
    entry_id = redis_client.xadd(STREAM_KEY, campos)
    return {"id": entry_id}


@router.get("/logs", response_model=list[LogEventOut])
def consultar_eventos(
    limit: int = Query(50, ge=1, le=1000),
    redis_client: Redis = Depends(get_redis),
    _admin: None = Depends(require_admin),
) -> list[LogEventOut]:
    # XREVRANGE já devolve do mais recente pro mais antigo — a ordem que uma
    # tela de auditoria quer (último evento primeiro).
    entradas = redis_client.xrevrange(STREAM_KEY, count=limit)
    return [
        LogEventOut(
            usuario_id=int(campos["usuario_id"]),
            acao=campos["acao"],
            timestamp=campos["timestamp"],
            ip=campos.get("ip") or None,
        )
        for _entry_id, campos in entradas
    ]
