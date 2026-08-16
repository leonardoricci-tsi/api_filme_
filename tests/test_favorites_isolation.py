from tests.conftest import auth_headers, registrar_usuario


def criar_favorito(client, token, tmdb_movie_id=13, titulo="Forrest Gump"):
    resposta = client.post(
        "/favorites",
        json={"tmdb_movie_id": tmdb_movie_id, "titulo": titulo, "poster_path": "/x.jpg"},
        headers=auth_headers(token),
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def test_criar_listar_deletar_favorito_do_proprio_usuario(client):
    token = registrar_usuario(client, email="dono@example.com")

    favorito = criar_favorito(client, token)

    resposta = client.get("/favorites", headers=auth_headers(token))
    assert resposta.status_code == 200
    assert len(resposta.json()) == 1

    resposta = client.delete(f"/favorites/{favorito['id']}", headers=auth_headers(token))
    assert resposta.status_code == 204

    resposta = client.get("/favorites", headers=auth_headers(token))
    assert resposta.json() == []


def test_favoritar_mesmo_filme_duas_vezes_retorna_409(client):
    token = registrar_usuario(client, email="dup_fav@example.com")
    criar_favorito(client, token, tmdb_movie_id=42)

    resposta = client.post(
        "/favorites",
        json={"tmdb_movie_id": 42, "titulo": "Qualquer", "poster_path": None},
        headers=auth_headers(token),
    )
    assert resposta.status_code == 409


def test_rota_de_favoritos_exige_autenticacao(client):
    resposta = client.get("/favorites")
    assert resposta.status_code == 401


def test_usuario_b_nao_ve_favorito_de_usuario_a_na_listagem(client):
    token_a = registrar_usuario(client, email="a@example.com")
    token_b = registrar_usuario(client, email="b@example.com")

    criar_favorito(client, token_a)

    resposta = client.get("/favorites", headers=auth_headers(token_b))
    assert resposta.status_code == 200
    assert resposta.json() == []


def test_usuario_b_nao_consegue_deletar_favorito_de_usuario_a(client):
    token_a = registrar_usuario(client, email="a2@example.com")
    token_b = registrar_usuario(client, email="b2@example.com")

    favorito_a = criar_favorito(client, token_a)

    resposta = client.delete(f"/favorites/{favorito_a['id']}", headers=auth_headers(token_b))
    assert resposta.status_code == 404

    # o favorito de A continua existindo
    resposta = client.get("/favorites", headers=auth_headers(token_a))
    assert len(resposta.json()) == 1
