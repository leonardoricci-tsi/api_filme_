from tests.conftest import auth_headers, registrar_usuario


def criar_comentario(
    client, token, tmdb_movie_id=13, titulo="Forrest Gump", texto="Ótimo filme!"
):
    resposta = client.post(
        "/comments",
        json={"tmdb_movie_id": tmdb_movie_id, "titulo": titulo, "texto": texto},
        headers=auth_headers(token),
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def test_criar_listar_deletar_comentario_do_proprio_usuario(client):
    token = registrar_usuario(client, email="dono_c@example.com")

    comentario = criar_comentario(client, token)
    assert comentario["titulo"] == "Forrest Gump"

    resposta = client.get(
        "/comments", params={"tmdb_movie_id": 13}, headers=auth_headers(token)
    )
    assert resposta.status_code == 200
    assert len(resposta.json()) == 1

    resposta = client.delete(f"/comments/{comentario['id']}", headers=auth_headers(token))
    assert resposta.status_code == 204

    resposta = client.get(
        "/comments", params={"tmdb_movie_id": 13}, headers=auth_headers(token)
    )
    assert resposta.json() == []


def test_rota_de_comentarios_exige_autenticacao(client):
    resposta = client.get("/comments", params={"tmdb_movie_id": 13})
    assert resposta.status_code == 401


def test_usuario_b_nao_ve_comentario_de_usuario_a_na_listagem(client):
    token_a = registrar_usuario(client, email="ac@example.com")
    token_b = registrar_usuario(client, email="bc@example.com")

    criar_comentario(client, token_a, tmdb_movie_id=99)

    resposta = client.get(
        "/comments", params={"tmdb_movie_id": 99}, headers=auth_headers(token_b)
    )
    assert resposta.status_code == 200
    assert resposta.json() == []


def test_usuario_b_nao_consegue_deletar_comentario_de_usuario_a(client):
    token_a = registrar_usuario(client, email="ac2@example.com")
    token_b = registrar_usuario(client, email="bc2@example.com")

    comentario_a = criar_comentario(client, token_a)

    resposta = client.delete(f"/comments/{comentario_a['id']}", headers=auth_headers(token_b))
    assert resposta.status_code == 404

    resposta = client.get(
        "/comments", params={"tmdb_movie_id": 13}, headers=auth_headers(token_a)
    )
    assert len(resposta.json()) == 1


def test_listar_todos_comentarios_do_usuario_sem_filtro_de_filme(client):
    token = registrar_usuario(client, email="multi_c@example.com")
    criar_comentario(client, token, tmdb_movie_id=13, titulo="Forrest Gump", texto="Top!")
    criar_comentario(client, token, tmdb_movie_id=857, titulo="Saving Private Ryan", texto="Ótimo!")

    resposta = client.get("/comments", headers=auth_headers(token))

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert len(corpo) == 2
    titulos = {c["titulo"] for c in corpo}
    assert titulos == {"Forrest Gump", "Saving Private Ryan"}


def test_listar_todos_comentarios_isola_por_usuario(client):
    token_a = registrar_usuario(client, email="all_a@example.com")
    token_b = registrar_usuario(client, email="all_b@example.com")

    criar_comentario(client, token_a, tmdb_movie_id=13, titulo="Forrest Gump")
    criar_comentario(client, token_b, tmdb_movie_id=857, titulo="Saving Private Ryan")

    resposta_a = client.get("/comments", headers=auth_headers(token_a))
    resposta_b = client.get("/comments", headers=auth_headers(token_b))

    assert len(resposta_a.json()) == 1
    assert resposta_a.json()[0]["titulo"] == "Forrest Gump"
    assert len(resposta_b.json()) == 1
    assert resposta_b.json()[0]["titulo"] == "Saving Private Ryan"
