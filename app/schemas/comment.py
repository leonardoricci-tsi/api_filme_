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
    nome_usuario: str | None
    texto: str
    criado_em: datetime
    # Computado por requisição (não é coluna): true só quando o comentário é
    # do usuario logado, pra frontend decidir se mostra o botão de apagar.
    meu: bool
