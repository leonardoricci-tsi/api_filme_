from pydantic import BaseModel


class MovieOut(BaseModel):
    tmdb_movie_id: int
    titulo: str
    sinopse: str
    poster_url: str | None
    data_lancamento: str | None
    nota: float | None = None


class PaginaFilmes(BaseModel):
    itens: list[MovieOut]
    total: int
    pagina: int
    tamanho_pagina: int
    total_paginas: int


class AtorOut(BaseModel):
    nome: str
    personagem: str
    foto_url: str | None


class ProvedorOut(BaseModel):
    nome: str
    logo_url: str | None
    tipo: str


class DetalhesFilmeOut(BaseModel):
    elenco: list[AtorOut]
    onde_assistir: list[ProvedorOut]
