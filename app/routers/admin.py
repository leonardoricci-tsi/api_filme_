from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.auth.dependencies import UsuarioAutenticado, require_admin
from app.database import get_db
from app.models import Comentario, Favorito
from app.openapi_responses import RESP_401, RESP_403_ADMIN, RESP_404, RESP_502_LOG_SERVICE
from app.routers.comments import _to_out
from app.schemas.comment import CommentOut
from app.schemas.favorite import AdminFavoriteOut
from app.services import log_client

router = APIRouter(prefix="/admin", tags=["admin"])

_RESP_ADMIN = RESP_401 | RESP_403_ADMIN


@router.get("/comments", response_model=list[CommentOut], responses=_RESP_ADMIN)
def listar_todos_comentarios(
    usuario_atual: UsuarioAutenticado = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[CommentOut]:
    """Só admin: lista comentários de TODOS os usuários (moderação), não só
    os do chamador — diferença de autorização que o `role` do JWT decide."""
    comentarios = db.query(Comentario).order_by(Comentario.criado_em.desc()).all()
    return [_to_out(c, usuario_atual.id) for c in comentarios]


@router.delete(
    "/comments/{comentario_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=_RESP_ADMIN | RESP_404,
)
def deletar_comentario_de_qualquer_usuario(
    comentario_id: int,
    request: Request,
    usuario_atual: UsuarioAutenticado = Depends(require_admin),
    db: Session = Depends(get_db),
) -> None:
    """Só admin: remove o comentário de QUALQUER usuário, sem checar
    ownership — ao contrário de DELETE /comments/{id}, que só apaga o
    próprio."""
    comentario = db.get(Comentario, comentario_id)
    if comentario is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recurso não encontrado")
    db.delete(comentario)
    db.commit()
    # "apagar comentário (moderação)": evento mínimo exigido pela
    # atividade 5 — usuario_id aqui é de quem moderou, não do autor.
    log_client.registrar_evento(
        usuario_atual.id,
        f"apagar_comentario_moderacao:{comentario_id}",
        ip=request.client.host if request.client else None,
    )


@router.get("/favorites", response_model=list[AdminFavoriteOut], responses=_RESP_ADMIN)
def listar_todos_favoritos(
    _usuario_atual: UsuarioAutenticado = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[Favorito]:
    """Só admin: lista favoritos de TODOS os usuários — mesma lógica de
    moderação de `GET /admin/comments`, agora pra favoritos."""
    return db.query(Favorito).order_by(Favorito.criado_em.desc()).all()


@router.delete(
    "/favorites/{favorito_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=_RESP_ADMIN | RESP_404,
)
def deletar_favorito_de_qualquer_usuario(
    favorito_id: int,
    _usuario_atual: UsuarioAutenticado = Depends(require_admin),
    db: Session = Depends(get_db),
) -> None:
    """Só admin: remove o favorito de QUALQUER usuário, sem checar
    ownership — ao contrário de DELETE /favorites/{id}, que só apaga o
    próprio."""
    favorito = db.get(Favorito, favorito_id)
    if favorito is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recurso não encontrado")
    db.delete(favorito)
    db.commit()


@router.get("/logs", responses=_RESP_ADMIN | RESP_502_LOG_SERVICE)
def consultar_logs(
    limit: int = Query(50, ge=1, le=1000),
    authorization: str | None = Header(None),
    _usuario_atual: UsuarioAutenticado = Depends(require_admin),
) -> JSONResponse:
    """Só admin: consulta os últimos N eventos de auditoria (atividade 5).

    Log-service não tem porta publicada pro host (mesmo princípio do
    auth-service), então essa rota é a única forma de um admin consultar o
    log de fora — o catálogo já barra com 403 quem não for admin
    (`require_admin`, mesmo enforcement da atividade 4) e repassa o header
    Authorization original pro log-service, que confere de novo com o
    mesmo JWT: defesa em profundidade, não round-trip redundante à toa."""
    try:
        resposta = log_client.consultar_eventos(limit, authorization)
    except log_client.LogServiceUnavailable as erro:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(erro)) from erro
    return JSONResponse(status_code=resposta.status_code, content=resposta.json())
