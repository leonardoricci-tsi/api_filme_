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
                        "vote_average": 8.475,
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
    pagina = resposta.json()
    assert pagina["total"] == 2
    assert pagina["pagina"] == 1
    assert pagina["tamanho_pagina"] == 20
    assert pagina["total_paginas"] == 1

    filmes = pagina["itens"]
    assert len(filmes) == 2
    forrest = next(f for f in filmes if f["tmdb_movie_id"] == 13)
    assert forrest["titulo"] == "Forrest Gump"
    assert forrest["poster_url"] == "https://image.tmdb.org/t/p/w500/poster1.jpg"
    assert forrest["nota"] == 8.475

    ryan = next(f for f in filmes if f["tmdb_movie_id"] == 857)
    assert ryan["poster_url"] is None
    assert ryan["nota"] is None


@respx.mock
def test_listar_filmes_empurra_sem_poster_pro_final(client):
    respx.get(f"{tmdb.TMDB_BASE_URL}/search/person").mock(
        return_value=Response(200, json={"results": [{"id": 31, "name": "Tom Hanks"}]})
    )
    respx.get(f"{tmdb.TMDB_BASE_URL}/person/31/movie_credits").mock(
        return_value=Response(
            200,
            json={
                "cast": [
                    # Lançamento mais recente, mas sem pôster — mesmo assim
                    # deve ir pro final da lista.
                    {
                        "id": 1,
                        "title": "Sem Poster",
                        "overview": "",
                        "poster_path": None,
                        "release_date": "2030-01-01",
                    },
                    {
                        "id": 2,
                        "title": "Com Poster Antigo",
                        "overview": "",
                        "poster_path": "/a.jpg",
                        "release_date": "1990-01-01",
                    },
                    {
                        "id": 3,
                        "title": "Com Poster Novo",
                        "overview": "",
                        "poster_path": "/b.jpg",
                        "release_date": "2020-01-01",
                    },
                ]
            },
        )
    )

    filmes = client.get("/movies").json()["itens"]

    assert [f["titulo"] for f in filmes] == ["Com Poster Novo", "Com Poster Antigo", "Sem Poster"]


@respx.mock
def test_listar_filmes_pagina_20_por_vez(client):
    respx.get(f"{tmdb.TMDB_BASE_URL}/search/person").mock(
        return_value=Response(200, json={"results": [{"id": 31, "name": "Tom Hanks"}]})
    )
    cast = [
        {
            "id": i,
            "title": f"Filme {i}",
            "overview": "",
            "poster_path": None,
            "release_date": f"20{i:02d}-01-01",
        }
        for i in range(25)
    ]
    respx.get(f"{tmdb.TMDB_BASE_URL}/person/31/movie_credits").mock(
        return_value=Response(200, json={"cast": cast})
    )

    primeira_pagina = client.get("/movies").json()
    assert len(primeira_pagina["itens"]) == 20
    assert primeira_pagina["total"] == 25
    assert primeira_pagina["total_paginas"] == 2

    segunda_pagina = client.get("/movies", params={"pagina": 2}).json()
    assert len(segunda_pagina["itens"]) == 5
    assert segunda_pagina["pagina"] == 2


@respx.mock
def test_listar_filmes_filtra_por_busca_no_titulo(client):
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
                        "overview": "",
                        "poster_path": None,
                        "release_date": "1994-07-06",
                    },
                    {
                        "id": 857,
                        "title": "Saving Private Ryan",
                        "overview": "",
                        "poster_path": None,
                        "release_date": "1998-07-24",
                    },
                ]
            },
        )
    )

    resposta = client.get("/movies", params={"busca": "forrest"})

    assert resposta.status_code == 200
    pagina = resposta.json()
    assert pagina["total"] == 1
    assert pagina["itens"][0]["titulo"] == "Forrest Gump"


@respx.mock
def test_listar_filmes_propaga_erro_da_tmdb_como_502(client):
    respx.get(f"{tmdb.TMDB_BASE_URL}/search/person").mock(return_value=Response(401))

    resposta = client.get("/movies")

    assert resposta.status_code == 502


@respx.mock
def test_detalhes_filme_retorna_elenco_e_onde_assistir(client):
    respx.get(f"{tmdb.TMDB_BASE_URL}/movie/13/credits").mock(
        return_value=Response(
            200,
            json={
                "cast": [
                    {"name": "Tom Hanks", "character": "Forrest Gump", "profile_path": "/th.jpg"},
                    {"name": "Robin Wright", "character": "Jenny Curran", "profile_path": None},
                ]
            },
        )
    )
    respx.get(f"{tmdb.TMDB_BASE_URL}/movie/13/watch/providers").mock(
        return_value=Response(
            200,
            json={
                "results": {
                    "BR": {
                        "flatrate": [{"provider_name": "Netflix", "logo_path": "/netflix.jpg"}],
                        "rent": [{"provider_name": "Google Play", "logo_path": None}],
                    },
                    "US": {"flatrate": [{"provider_name": "Should not appear"}]},
                }
            },
        )
    )

    resposta = client.get("/movies/13/detalhes")

    assert resposta.status_code == 200
    corpo = resposta.json()

    assert len(corpo["elenco"]) == 2
    assert corpo["elenco"][0] == {
        "nome": "Tom Hanks",
        "personagem": "Forrest Gump",
        "foto_url": "https://image.tmdb.org/t/p/w500/th.jpg",
    }

    assert corpo["onde_assistir"] == [
        {
            "nome": "Netflix",
            "logo_url": "https://image.tmdb.org/t/p/w500/netflix.jpg",
            "tipo": "assinatura",
        },
        {"nome": "Google Play", "logo_url": None, "tipo": "aluguel"},
    ]


@respx.mock
def test_detalhes_filme_propaga_erro_da_tmdb_como_502(client):
    respx.get(f"{tmdb.TMDB_BASE_URL}/movie/13/credits").mock(return_value=Response(404))

    resposta = client.get("/movies/13/detalhes")

    assert resposta.status_code == 502
