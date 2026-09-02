import io

import respx
from httpx import Response
from PIL import Image

from app.services import tmdb
from tests.conftest import auth_headers, criar_token


def setup_function():
    tmdb._person_id_cache = None
    tmdb._movies_cache = None
    tmdb._movies_cache_expira_em = 0.0


# --- quiz do pôster pixelado: exclusivo de stalker_do_tomhanks (e admin, que herda) ---

_CAST_QUIZ = [
    {
        "id": i,
        "title": titulo,
        "overview": f"Sinopse de {titulo}.",
        "poster_path": f"/poster{i}.jpg",
        "release_date": "2000-01-01",
        "vote_average": 7.5,
    }
    for i, titulo in enumerate(
        ["Forrest Gump", "Cast Away", "Big", "A Toy Story", "The Terminal"], start=1
    )
]


def _mockar_tmdb_para_quiz():
    respx.get(f"{tmdb.TMDB_BASE_URL}/search/person").mock(
        return_value=Response(200, json={"results": [{"id": 31, "name": "Tom Hanks"}]})
    )
    respx.get(f"{tmdb.TMDB_BASE_URL}/person/31/movie_credits").mock(
        return_value=Response(200, json={"cast": _CAST_QUIZ})
    )

    buffer = io.BytesIO()
    Image.new("RGB", (20, 20), color="red").save(buffer, format="PNG")
    respx.get(url__regex=r"https://image\.tmdb\.org/.*").mock(
        return_value=Response(200, content=buffer.getvalue())
    )


def test_cinefilo_nao_acessa_quiz(client):
    token = criar_token(role="cinefilo")

    resposta = client.get("/quiz/pixelado", headers=auth_headers(token))

    assert resposta.status_code == 403


def test_nerd_nao_acessa_quiz(client):
    """Quiz é exclusivo do topo da escada — nerd não é suficiente."""
    token = criar_token(role="nerd")

    resposta = client.get("/quiz/pixelado", headers=auth_headers(token))

    assert resposta.status_code == 403


@respx.mock
def test_admin_tambem_acessa_quiz(client):
    _mockar_tmdb_para_quiz()
    token = criar_token(role="admin")

    resposta = client.get("/quiz/pixelado", headers=auth_headers(token))

    assert resposta.status_code == 200


@respx.mock
def test_stalker_acessa_quiz_e_recebe_4_opcoes(client):
    _mockar_tmdb_para_quiz()
    token = criar_token(role="stalker_do_tomhanks")

    resposta = client.get("/quiz/pixelado", headers=auth_headers(token))

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert len(corpo["opcoes"]) == 4
    assert len(set(corpo["opcoes"])) == 4
    assert corpo["imagem_base64"]
    assert corpo["round_id"]


@respx.mock
def test_stalker_acerta_resposta_do_quiz(client):
    _mockar_tmdb_para_quiz()
    token = criar_token(role="stalker_do_tomhanks")

    rodada = client.get("/quiz/pixelado", headers=auth_headers(token)).json()
    # A resposta certa não vem na rodada — só descobrimos consultando o
    # endpoint de checagem, que sempre devolve `resposta_certa`.
    checagem = client.post(
        "/quiz/pixelado/resposta",
        json={"round_id": rodada["round_id"], "resposta": rodada["opcoes"][0]},
        headers=auth_headers(token),
    ).json()

    resposta_final = client.post(
        "/quiz/pixelado/resposta",
        json={"round_id": rodada["round_id"], "resposta": checagem["resposta_certa"]},
        headers=auth_headers(token),
    )

    assert resposta_final.status_code == 200
    corpo = resposta_final.json()
    assert corpo["correto"] is True
    assert corpo["sinopse"] == f"Sinopse de {corpo['resposta_certa']}."
    assert corpo["poster_url"] is not None
    assert corpo["data_lancamento"] == "2000-01-01"
    assert corpo["nota"] == 7.5


@respx.mock
def test_stalker_erra_resposta_do_quiz(client):
    _mockar_tmdb_para_quiz()
    token = criar_token(role="stalker_do_tomhanks")

    rodada = client.get("/quiz/pixelado", headers=auth_headers(token)).json()

    resposta = client.post(
        "/quiz/pixelado/resposta",
        json={"round_id": rodada["round_id"], "resposta": "Título que não existe"},
        headers=auth_headers(token),
    )

    assert resposta.status_code == 200
    assert resposta.json()["correto"] is False


def test_round_id_invalido_e_recusado(client):
    token = criar_token(role="stalker_do_tomhanks")

    resposta = client.post(
        "/quiz/pixelado/resposta",
        json={"round_id": "token-forjado", "resposta": "Forrest Gump"},
        headers=auth_headers(token),
    )

    assert resposta.status_code == 400
