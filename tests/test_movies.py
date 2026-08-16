import respx
from httpx import Response

from app.services import tmdb


def setup_function():
    # Garante que os caches em memória não vazam entre testes
    tmdb._person_id_cache = None
    tmdb._movies_cache = None
    tmdb._movies_cache_expira_em = 0.0


@respx.mock
def test_listar_filmes_retorna_dados_ao_vivo_da_tmdb(client):
    respx.get(f"{tmdb.TMDB_BASE_URL}/search/person").mock(
        return_value=Response(200, json={"results": [{"id": 31, "name": "Tom Hanks"}]})
    )
    respx.get(f"{tmdb.TMDB_BASE_URL}/person/31/movie_credits").mock(
        return_value=Response(
            200,
            json={
                "cast": [
                    {
                        "id": 13,
                        "title": "Forrest Gump",
                        "overview": "Um homem simples...",
                        "poster_path": "/poster1.jpg",
                        "release_date": "1994-07-06",
                    },
                    {
                        "id": 857,
                        "title": "Saving Private Ryan",
                        "overview": "Um capitão...",
                        "poster_path": None,
                        "release_date": "1998-07-24",
                    },
                ]
            },
        )
    )

    resposta = client.get("/movies")

    assert resposta.status_code == 200
    filmes = resposta.json()
    assert len(filmes) == 2
    forrest = next(f for f in filmes if f["tmdb_movie_id"] == 13)
    assert forrest["titulo"] == "Forrest Gump"
    assert forrest["poster_url"] == "https://image.tmdb.org/t/p/w500/poster1.jpg"

    ryan = next(f for f in filmes if f["tmdb_movie_id"] == 857)
    assert ryan["poster_url"] is None


@respx.mock
def test_listar_filmes_propaga_erro_da_tmdb_como_502(client):
    respx.get(f"{tmdb.TMDB_BASE_URL}/search/person").mock(return_value=Response(401))

    resposta = client.get("/movies")

    assert resposta.status_code == 502
