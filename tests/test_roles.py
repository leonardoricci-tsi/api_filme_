from tests.conftest import auth_headers, criar_token

# --- hierarquia cinefilo < nerd < stalker_do_tomhanks < admin em /comments e /favorites ---


def test_cinefilo_nao_comenta(client):
    token = criar_token(role="cinefilo")

    resposta = client.post(
        "/comments",
        json={"tmdb_movie_id": 13, "titulo": "Forrest Gump", "texto": "Bom!"},
        headers=auth_headers(token),
    )

    assert resposta.status_code == 403


def test_cinefilo_nao_favorita(client):
    token = criar_token(role="cinefilo")

    resposta = client.post(
        "/favorites",
        json={"tmdb_movie_id": 13, "titulo": "Forrest Gump", "poster_path": "/p.jpg"},
        headers=auth_headers(token),
    )

    assert resposta.status_code == 403


def test_nerd_comenta_e_favorita(client):
    token = criar_token(role="nerd")

    resposta_comentario = client.post(
        "/comments",
        json={"tmdb_movie_id": 13, "titulo": "Forrest Gump", "texto": "Bom!"},
        headers=auth_headers(token),
    )
    resposta_favorito = client.post(
        "/favorites",
        json={"tmdb_movie_id": 13, "titulo": "Forrest Gump", "poster_path": "/p.jpg"},
        headers=auth_headers(token),
    )

    assert resposta_comentario.status_code == 201
    assert resposta_favorito.status_code == 201


def test_stalker_tambem_comenta_e_favorita(client):
    """Papel mais alto inclui a permissão dos de baixo: stalker_do_tomhanks
    também pode fazer tudo que nerd faz."""
    token = criar_token(role="stalker_do_tomhanks")

    resposta_comentario = client.post(
        "/comments",
        json={"tmdb_movie_id": 13, "titulo": "Forrest Gump", "texto": "Bom!"},
        headers=auth_headers(token),
    )

    assert resposta_comentario.status_code == 201


def test_admin_tambem_comenta_e_favorita(client):
    """admin é o topo da escada: consome tudo que stalker_do_tomhanks
    consome, além de moderar."""
    token = criar_token(role="admin")

    resposta_comentario = client.post(
        "/comments",
        json={"tmdb_movie_id": 13, "titulo": "Forrest Gump", "texto": "Bom!"},
        headers=auth_headers(token),
    )
    resposta_favorito = client.post(
        "/favorites",
        json={"tmdb_movie_id": 13, "titulo": "Forrest Gump", "poster_path": "/p.jpg"},
        headers=auth_headers(token),
    )

    assert resposta_comentario.status_code == 201
    assert resposta_favorito.status_code == 201
