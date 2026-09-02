from tests.conftest import auth_headers, criar_token


def criar_comentario(client, token, tmdb_movie_id=13, titulo="Forrest Gump", texto="Bom!"):
    resposta = client.post(
        "/comments",
        json={"tmdb_movie_id": tmdb_movie_id, "titulo": titulo, "texto": texto},
        headers=auth_headers(token),
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def test_usuario_comum_nao_acessa_rota_admin(client):
    token = criar_token(role="nerd")

    resposta = client.get("/admin/comments", headers=auth_headers(token))

    assert resposta.status_code == 403


def test_admin_lista_comentarios_de_todos_os_usuarios(client):
    token_a = criar_token(role="nerd")
    token_b = criar_token(role="nerd")
    token_admin = criar_token(role="admin")

    criar_comentario(client, token_a, titulo="Comentário de A")
    criar_comentario(client, token_b, titulo="Comentário de B")

    resposta = client.get("/admin/comments", headers=auth_headers(token_admin))

    assert resposta.status_code == 200
    titulos = {c["titulo"] for c in resposta.json()}
    assert titulos == {"Comentário de A", "Comentário de B"}


def test_usuario_comum_nao_consegue_deletar_comentario_de_outro_via_rota_admin(client):
    token_a = criar_token(role="nerd")
    token_b = criar_token(role="nerd")
    comentario_a = criar_comentario(client, token_a)

    resposta = client.delete(f"/admin/comments/{comentario_a['id']}", headers=auth_headers(token_b))

    assert resposta.status_code == 403


def test_admin_deleta_comentario_de_qualquer_usuario(client):
    token_a = criar_token(role="nerd")
    token_admin = criar_token(role="admin")
    comentario_a = criar_comentario(client, token_a)

    resposta = client.delete(
        f"/admin/comments/{comentario_a['id']}", headers=auth_headers(token_admin)
    )

    assert resposta.status_code == 204
    resposta = client.get("/comments", headers=auth_headers(token_a))
    assert resposta.json() == []
