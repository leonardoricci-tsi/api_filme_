from pydantic import BaseModel


class MovieOut(BaseModel):
    tmdb_movie_id: int
    titulo: str
    sinopse: str
    poster_url: str | None
    data_lancamento: str | None
