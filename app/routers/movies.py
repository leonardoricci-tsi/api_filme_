from fastapi import APIRouter, HTTPException, status

from app.schemas.movie import MovieOut
from app.services.tmdb import TMDBError, get_tom_hanks_movies

router = APIRouter(tags=["movies"])


@router.get("/movies", response_model=list[MovieOut])
def listar_filmes() -> list[MovieOut]:
    try:
        filmes = get_tom_hanks_movies()
    except TMDBError as erro:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=str(erro)
        ) from erro
    return filmes
