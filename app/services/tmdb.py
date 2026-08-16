import time

import httpx

from app.config import get_settings

TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"
ATOR_BUSCADO = "Tom Hanks"

# TTL do cache em memória da listagem de filmes (dado nunca é persistido em
# tabela — só evita repetir o round-trip à TMDB a cada catálogo aberto).
MOVIES_CACHE_TTL_SECONDS = 300

# Client HTTP reaproveitado entre chamadas: evita refazer handshake TLS
# (que sozinho já custa ~200-400ms) a cada requisição a /movies.
_http_client: httpx.Client | None = None

_person_id_cache: int | None = None
_movies_cache: list[dict] | None = None
_movies_cache_expira_em: float = 0.0


class TMDBError(Exception):
    """Erro ao consumir a API do TMDB (rede, chave inválida, resposta inesperada)."""


def _get_http_client() -> httpx.Client:
    global _http_client
    if _http_client is None:
        _http_client = httpx.Client(timeout=10.0)
    return _http_client


def _build_poster_url(poster_path: str | None) -> str | None:
    if not poster_path:
        return None
    return f"{TMDB_IMAGE_BASE_URL}{poster_path}"


def _get_tom_hanks_person_id(client: httpx.Client) -> int:
    global _person_id_cache
    if _person_id_cache is not None:
        return _person_id_cache

    settings = get_settings()
    resposta = client.get(
        f"{TMDB_BASE_URL}/search/person",
        params={"query": ATOR_BUSCADO, "api_key": settings.tmdb_api_key},
    )
    if resposta.status_code != 200:
        raise TMDBError(f"Falha ao buscar person_id no TMDB: HTTP {resposta.status_code}")

    resultados = resposta.json().get("results", [])
    if not resultados:
        raise TMDBError(f"Nenhuma pessoa encontrada no TMDB para '{ATOR_BUSCADO}'")

    _person_id_cache = resultados[0]["id"]
    return _person_id_cache


def get_tom_hanks_movies() -> list[dict]:
    """Busca ao vivo na TMDB os filmes do Tom Hanks. Nunca persiste em tabela —
    apenas cacheia em memória por alguns minutos para evitar round-trips repetidos."""
    global _movies_cache, _movies_cache_expira_em

    agora = time.monotonic()
    if _movies_cache is not None and agora < _movies_cache_expira_em:
        return _movies_cache

    settings = get_settings()
    client = _get_http_client()

    person_id = _get_tom_hanks_person_id(client)

    resposta = client.get(
        f"{TMDB_BASE_URL}/person/{person_id}/movie_credits",
        params={"api_key": settings.tmdb_api_key},
    )
    if resposta.status_code != 200:
        raise TMDBError(f"Falha ao buscar movie_credits no TMDB: HTTP {resposta.status_code}")

    elenco = resposta.json().get("cast", [])

    filmes_por_id: dict[int, dict] = {}
    for item in elenco:
        tmdb_movie_id = item.get("id")
        if tmdb_movie_id is None or tmdb_movie_id in filmes_por_id:
            continue
        filmes_por_id[tmdb_movie_id] = {
            "tmdb_movie_id": tmdb_movie_id,
            "titulo": item.get("title") or item.get("original_title") or "",
            "sinopse": item.get("overview") or "",
            "poster_url": _build_poster_url(item.get("poster_path")),
            "data_lancamento": item.get("release_date") or None,
        }

    filmes = list(filmes_por_id.values())
    filmes.sort(key=lambda f: f["data_lancamento"] or "", reverse=True)

    _movies_cache = filmes
    _movies_cache_expira_em = agora + MOVIES_CACHE_TTL_SECONDS
    return filmes
