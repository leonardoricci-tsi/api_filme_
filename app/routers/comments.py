from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import UsuarioAutenticado, get_current_user
from app.database import get_db
from app.models import Comentario
from app.routers._ownership import get_owned_or_404
from app.schemas.comment import CommentIn, CommentOut

router = APIRouter(prefix="/comments", tags=["comments"])


def _to_out(comentario: Comentario, usuario_atual_id: int) -> CommentOut:
    return CommentOut(
        id=comentario.id,
        tmdb_movie_id=comentario.tmdb_movie_id,
        titulo=comentario.titulo,
        poster_path=comentario.poster_path,
        nome_usuario=comentario.nome_usuario,
        texto=comentario.texto,
        criado_em=comentario.criado_em,
        meu=comentario.usuario_id == usuario_atual_id,
    )


@router.post("", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
def criar_comentario(
    dados: CommentIn,
    usuario_atual: UsuarioAutenticado = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CommentOut:
    comentario = Comentario(
        usuario_id=usuario_atual.id,
        tmdb_movie_id=dados.tmdb_movie_id,
        titulo=dados.titulo,
        poster_path=dados.poster_path,
        nome_usuario=usuario_atual.nome,
        texto=dados.texto,
    )
    db.add(comentario)
    db.commit()
    return _to_out(comentario, usuario_atual.id)


@router.get("", response_model=list[CommentOut])
def listar_comentarios(
    tmdb_movie_id: int | None = Query(None),
    usuario_atual: UsuarioAutenticado = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[CommentOut]:
    query = db.query(Comentario)
    if tmdb_movie_id is not None:
        # Comentários de um filme são uma conversa pública: todo mundo vê o
        # comentário (e o nome) de todo mundo, não só o próprio.
        query = query.filter(Comentario.tmdb_movie_id == tmdb_movie_id)
    else:
        # Sem filtro de filme = "meus comentários" (histórico pessoal,
        # privado — usado pela tela de Comentários do menu).
        query = query.filter(Comentario.usuario_id == usuario_atual.id)

    comentarios = query.order_by(Comentario.criado_em.desc()).all()
    return [_to_out(c, usuario_atual.id) for c in comentarios]


@router.delete("/{comentario_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_comentario(
    comentario_id: int,
    usuario_atual: UsuarioAutenticado = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    comentario = get_owned_or_404(db, Comentario, comentario_id, usuario_atual.id)
    db.delete(comentario)
    db.commit()
