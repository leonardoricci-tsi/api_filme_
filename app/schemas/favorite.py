from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FavoriteIn(BaseModel):
    tmdb_movie_id: int
    titulo: str = Field(min_length=1, max_length=500)
    poster_path: str | None = None


class FavoriteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tmdb_movie_id: int
    titulo: str
    poster_path: str | None
    criado_em: datetime


class AdminFavoriteOut(FavoriteOut):
    """Só pra listagem de moderação (`GET /admin/favorites`) — expõe de
    quem é o favorito, já que ali não é "os meus", é "os de todo mundo"."""

    usuario_id: int
