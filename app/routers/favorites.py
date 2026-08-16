from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models import Favorito, Usuario
from app.routers._ownership import get_owned_or_404
from app.schemas.favorite import FavoriteIn, FavoriteOut

router = APIRouter(prefix="/favorites", tags=["favorites"])


@router.post("", response_model=FavoriteOut, status_code=status.HTTP_201_CREATED)
def criar_favorito(
    dados: FavoriteIn,
    usuario_atual: Usuario = Depends(get_current_user),
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
    return favorito


@router.get("", response_model=list[FavoriteOut])
def listar_favoritos(
    usuario_atual: Usuario = Depends(get_current_user),
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
    usuario_atual: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    favorito = get_owned_or_404(db, Favorito, favorito_id, usuario_atual.id)
    db.delete(favorito)
    db.commit()
