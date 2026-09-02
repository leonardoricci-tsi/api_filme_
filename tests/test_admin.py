import respx
from httpx import Response

from tests.conftest import auth_headers, criar_token


def criar_comentario(client, token, tmdb_movie_id=13, titulo="Forrest Gump", texto="Bom!"):
    resposta = client.post(
        "/comments",
        json={"tmdb_movie_id": tmdb_movie_id, "titulo": titulo, "texto": texto},
        headers=auth_headers(token),
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def criar_favorito(client, token, tmdb_movie_id=13, titulo="Forrest Gump"):
    resposta = client.post(
        "/favorites",
        json={"tmdb_movie_id": tmdb_movie_id, "titulo": titulo, "poster_path": "/p.jpg"},
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


def test_usuario_comum_nao_acessa_admin_favorites(client):
    token = criar_token(role="nerd")

    resposta = client.get("/admin/favorites", headers=auth_headers(token))

    assert resposta.status_code == 403


def test_admin_lista_favoritos_de_todos_os_usuarios(client):
    token_a = criar_token(role="nerd")
    token_b = criar_token(role="nerd")
    token_admin = criar_token(role="admin")

    criar_favorito(client, token_a, tmdb_movie_id=13, titulo="Forrest Gump")
    criar_favorito(client, token_b, tmdb_movie_id=857, titulo="Saving Private Ryan")

    resposta = client.get("/admin/favorites", headers=auth_headers(token_admin))

    assert resposta.status_code == 200
    titulos = {f["titulo"] for f in resposta.json()}
    assert titulos == {"Forrest Gump", "Saving Private Ryan"}
    # listagem de moderação expõe de quem é cada favorito
    assert all("usuario_id" in f for f in resposta.json())


def test_usuario_comum_nao_consegue_deletar_favorito_de_outro_via_rota_admin(client):
    token_a = criar_token(role="nerd")
    token_b = criar_token(role="nerd")
    favorito_a = criar_favorito(client, token_a)

    resposta = client.delete(f"/admin/favorites/{favorito_a['id']}", headers=auth_headers(token_b))

    assert resposta.status_code == 403


def test_admin_deleta_favorito_de_qualquer_usuario(client):
    token_a = criar_token(role="nerd")
    token_admin = criar_token(role="admin")
    favorito_a = criar_favorito(client, token_a)

    resposta = client.delete(
        f"/admin/favorites/{favorito_a['id']}", headers=auth_headers(token_admin)
    )

    assert resposta.status_code == 204
    resposta = client.get("/favorites", headers=auth_headers(token_a))
    assert resposta.json() == []


# --- admin: promover/rebaixar papel de usuário (proxy pro auth-service) ---


@respx.mock
def test_admin_lista_usuarios(client):
    from app.config import get_settings

    auth_url = get_settings().auth_service_url
    respx.get(f"{auth_url}/auth/admin/users").mock(
        return_value=Response(
            200,
            json=[
                {
                    "id": 1,
                    "nome": "Ana",
                    "email": "ana@example.com",
                    "role": "cinefilo",
                    "criado_em": "2026-01-01T00:00:00",
                }
            ],
        )
    )
    token = criar_token(role="admin")

    resposta = client.get("/auth/admin/users", headers=auth_headers(token))

    assert resposta.status_code == 200
    assert resposta.json()[0]["role"] == "cinefilo"


@respx.mock
def test_admin_promove_usuario(client):
    from app.config import get_settings

    auth_url = get_settings().auth_service_url
    rota_mock = respx.patch(f"{auth_url}/auth/admin/users/1/role").mock(
        return_value=Response(
            200,
            json={
                "id": 1,
                "nome": "Ana",
                "email": "ana@example.com",
                "role": "stalker_do_tomhanks",
                "criado_em": "2026-01-01T00:00:00",
            },
        )
    )
    token = criar_token(role="admin")

    resposta = client.patch(
        "/auth/admin/users/1/role",
        json={"role": "stalker_do_tomhanks"},
        headers=auth_headers(token),
    )

    assert resposta.status_code == 200
    assert resposta.json()["role"] == "stalker_do_tomhanks"
    assert rota_mock.calls.last.request.headers["Authorization"] == auth_headers(token)["Authorization"]
