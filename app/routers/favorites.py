from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.dependencies import UsuarioAutenticado, require_papel_minimo
from app.database import get_db
from app.models import Favorito
from app.routers._ownership import get_owned_or_404
from app.schemas.favorite import FavoriteIn, FavoriteOut
from app.services import log_client

router = APIRouter(prefix="/favorites", tags=["favorites"])


@router.post("", response_model=FavoriteOut, status_code=status.HTTP_201_CREATED)
def criar_favorito(
    dados: FavoriteIn,
    request: Request,
    usuario_atual: UsuarioAutenticado = Depends(require_papel_minimo("nerd")),
    db: Session = Depends(get_db),
) -> FavoriteOut:
    favorito = Favorito(
        usuario_id=usuario_atual.id,
        tmdb_movie_id=dados.tmdb_movie_id,
        titulo=dados.titulo,
        poster_path=dados.poster_path,
    )
    db.add(favorito)
    try:
        db.commit()
    except IntegrityError as erro:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Filme já favoritado"
        ) from erro
    # Evento mínimo exigido pela atividade 5.
    log_client.registrar_evento(
        usuario_atual.id,
        f"favoritar_filme:{dados.tmdb_movie_id}",
        ip=request.client.host if request.client else None,
    )
    return favorito


@router.get("", response_model=list[FavoriteOut])
def listar_favoritos(
    usuario_atual: UsuarioAutenticado = Depends(require_papel_minimo("nerd")),
    db: Session = Depends(get_db),
) -> list[FavoriteOut]:
    return (
        db.query(Favorito)
        .filter(Favorito.usuario_id == usuario_atual.id)
        .order_by(Favorito.criado_em.desc())
        .all()
    )


@router.delete("/{favorito_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_favorito(
    favorito_id: int,
    usuario_atual: UsuarioAutenticado = Depends(require_papel_minimo("nerd")),
    db: Session = Depends(get_db),
) -> None:
    favorito = get_owned_or_404(db, Favorito, favorito_id, usuario_atual.id)
    db.delete(favorito)
    db.commit()
