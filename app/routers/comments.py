from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models import Comentario, Usuario
from app.routers._ownership import get_owned_or_404
from app.schemas.comment import CommentIn, CommentOut

router = APIRouter(prefix="/comments", tags=["comments"])


@router.post("", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
def criar_comentario(
    dados: CommentIn,
    usuario_atual: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CommentOut:
    comentario = Comentario(
        usuario_id=usuario_atual.id,
        tmdb_movie_id=dados.tmdb_movie_id,
        titulo=dados.titulo,
        poster_path=dados.poster_path,
        texto=dados.texto,
    )
    db.add(comentario)
    db.commit()
    return comentario


@router.get("", response_model=list[CommentOut])
def listar_comentarios(
    tmdb_movie_id: int | None = Query(None),
    usuario_atual: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[CommentOut]:
    query = db.query(Comentario).filter(Comentario.usuario_id == usuario_atual.id)
    if tmdb_movie_id is not None:
        query = query.filter(Comentario.tmdb_movie_id == tmdb_movie_id)
    return query.order_by(Comentario.criado_em.desc()).all()


@router.delete("/{comentario_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_comentario(
    comentario_id: int,
    usuario_atual: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    comentario = get_owned_or_404(db, Comentario, comentario_id, usuario_atual.id)
    db.delete(comentario)
    db.commit()
