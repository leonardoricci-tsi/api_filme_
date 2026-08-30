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


def _build_imagem_url(caminho: str | None) -> str | None:
    if not caminho:
        return None
    return f"{TMDB_IMAGE_BASE_URL}{caminho}"


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
            "poster_url": _build_imagem_url(item.get("poster_path")),
            "data_lancamento": item.get("release_date") or None,
            "nota": item.get("vote_average"),
        }

    filmes = list(filmes_por_id.values())
    filmes.sort(key=lambda f: f["data_lancamento"] or "", reverse=True)
    # Ordenação estável: preserva a ordem por data acima, só empurra os sem
    # pôster pro final da lista (e, por consequência, pras últimas páginas).
    filmes.sort(key=lambda f: f["poster_url"] is None)

    _movies_cache = filmes
    _movies_cache_expira_em = agora + MOVIES_CACHE_TTL_SECONDS
    return filmes


# Tipo do provedor de streaming, mapeado pra categoria da resposta da TMDB.
_TIPOS_PROVEDOR = (("assinatura", "flatrate"), ("aluguel", "rent"), ("compra", "buy"))


def get_movie_detalhes(tmdb_movie_id: int) -> dict:
    """Busca ao vivo na TMDB o elenco principal e onde assistir (região BR)
    de um filme específico. Não é cacheado — só é chamado quando o usuário
    abre os detalhes de um filme, então o volume de chamadas é bem menor
    que o da listagem principal."""
    settings = get_settings()
    client = _get_http_client()

    resposta_elenco = client.get(
        f"{TMDB_BASE_URL}/movie/{tmdb_movie_id}/credits",
        params={"api_key": settings.tmdb_api_key},
    )
    if resposta_elenco.status_code != 200:
        raise TMDBError(f"Falha ao buscar elenco no TMDB: HTTP {resposta_elenco.status_code}")

    elenco = [
        {
            "nome": ator.get("name") or "",
            "personagem": ator.get("character") or "",
            "foto_url": _build_imagem_url(ator.get("profile_path")),
        }
        for ator in resposta_elenco.json().get("cast", [])[:10]
    ]

    resposta_provedores = client.get(
        f"{TMDB_BASE_URL}/movie/{tmdb_movie_id}/watch/providers",
        params={"api_key": settings.tmdb_api_key},
    )
    if resposta_provedores.status_code != 200:
        raise TMDBError(
            f"Falha ao buscar onde assistir no TMDB: HTTP {resposta_provedores.status_code}"
        )

    provedores_brasil = resposta_provedores.json().get("results", {}).get("BR", {})
    onde_assistir = [
        {
            "nome": provedor.get("provider_name") or "",
            "logo_url": _build_imagem_url(provedor.get("logo_path")),
            "tipo": tipo,
        }
        for tipo, chave in _TIPOS_PROVEDOR
        for provedor in provedores_brasil.get(chave, [])
    ]

    return {"elenco": elenco, "onde_assistir": onde_assistir}
