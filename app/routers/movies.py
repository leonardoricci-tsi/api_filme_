import math

from fastapi import APIRouter, HTTPException, Query, status

from app.openapi_responses import RESP_502_TMDB
from app.schemas.movie import DetalhesFilmeOut, PaginaFilmes
from app.services.tmdb import TMDBError, get_movie_detalhes, get_tom_hanks_movies

router = APIRouter(tags=["movies"])

TAMANHO_PAGINA = 20


@router.get("/movies", response_model=PaginaFilmes, responses=RESP_502_TMDB)
def listar_filmes(pagina: int = Query(1, ge=1), busca: str = Query("")) -> PaginaFilmes:
    try:
        filmes = get_tom_hanks_movies()
    except TMDBError as erro:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=str(erro)
        ) from erro

    termo = busca.strip().lower()
    if termo:
        filmes = [f for f in filmes if termo in f["titulo"].lower()]

    total = len(filmes)
    total_paginas = max(1, math.ceil(total / TAMANHO_PAGINA))
    inicio = (pagina - 1) * TAMANHO_PAGINA

    return PaginaFilmes(
        itens=filmes[inicio : inicio + TAMANHO_PAGINA],
        total=total,
        pagina=pagina,
        tamanho_pagina=TAMANHO_PAGINA,
        total_paginas=total_paginas,
    )


@router.get("/movies/{tmdb_movie_id}/detalhes", response_model=DetalhesFilmeOut, responses=RESP_502_TMDB)
def detalhes_filme(tmdb_movie_id: int) -> DetalhesFilmeOut:
    try:
        detalhes = get_movie_detalhes(tmdb_movie_id)
    except TMDBError as erro:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=str(erro)
        ) from erro
    return DetalhesFilmeOut(**detalhes)
