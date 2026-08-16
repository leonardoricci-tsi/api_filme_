from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CommentIn(BaseModel):
    tmdb_movie_id: int
    titulo: str = Field(min_length=1, max_length=500)
    poster_path: str | None = None
    texto: str = Field(min_length=1)


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tmdb_movie_id: int
    titulo: str | None
    poster_path: str | None
    texto: str
    criado_em: datetime
