from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import UsuarioAutenticado, require_admin
from app.database import get_db
from app.models import Comentario, Favorito
from app.routers.comments import _to_out
from app.schemas.comment import CommentOut
from app.schemas.favorite import AdminFavoriteOut

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/comments", response_model=list[CommentOut])
def listar_todos_comentarios(
    usuario_atual: UsuarioAutenticado = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[CommentOut]:
    """Só admin: lista comentários de TODOS os usuários (moderação), não só
    os do chamador — diferença de autorização que o `role` do JWT decide."""
    comentarios = db.query(Comentario).order_by(Comentario.criado_em.desc()).all()
    return [_to_out(c, usuario_atual.id) for c in comentarios]


@router.delete("/comments/{comentario_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_comentario_de_qualquer_usuario(
    comentario_id: int,
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


@router.get("/favorites", response_model=list[AdminFavoriteOut])
def listar_todos_favoritos(
    _usuario_atual: UsuarioAutenticado = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[Favorito]:
    """Só admin: lista favoritos de TODOS os usuários — mesma lógica de
    moderação de `GET /admin/comments`, agora pra favoritos."""
    return db.query(Favorito).order_by(Favorito.criado_em.desc()).all()


@router.delete("/favorites/{favorito_id}", status_code=status.HTTP_204_NO_CONTENT)
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
