"""O benefício do plano premium (atividade 7): mesma ação, dois resultados
— igual à atividade 4 fez com os papéis, mas aqui quem decide é a tabela
`assinaturas`, não o papel do JWT."""

from app.models import Assinatura
from app.routers.premium import LIMITE_FAVORITOS_GRATIS
from tests.conftest import auth_headers, criar_token


def favoritar(client, token, tmdb_movie_id):
    return client.post(
        "/favorites",
        json={"tmdb_movie_id": tmdb_movie_id, "titulo": f"Filme {tmdb_movie_id}", "poster_path": None},
        headers=auth_headers(token),
    )


def tornar_premium(db_session, usuario_id):
    db_session.add(Assinatura(usuario_id=usuario_id, premium=True))
    db_session.commit()


def test_usuario_comum_para_no_limite_de_favoritos(client):
    token = criar_token(usuario_id=60)
    for filme in range(1, LIMITE_FAVORITOS_GRATIS + 1):
        assert favoritar(client, token, filme).status_code == 201

    resposta = favoritar(client, token, 999)

    assert resposta.status_code == 403
    assert "plano Cinéfilo" in resposta.json()["detail"]
    assert len(client.get("/favorites", headers=auth_headers(token)).json()) == LIMITE_FAVORITOS_GRATIS


def test_premium_passa_do_limite(client, db_session):
    tornar_premium(db_session, 61)
    token = criar_token(usuario_id=61)

    for filme in range(1, LIMITE_FAVORITOS_GRATIS + 3):
        assert favoritar(client, token, filme).status_code == 201

    assert len(client.get("/favorites", headers=auth_headers(token)).json()) == LIMITE_FAVORITOS_GRATIS + 2


def test_apagar_um_favorito_libera_vaga_pro_usuario_comum(client):
    token = criar_token(usuario_id=62)
    ids = [favoritar(client, token, filme).json()["id"] for filme in range(1, LIMITE_FAVORITOS_GRATIS + 1)]
    assert favoritar(client, token, 999).status_code == 403

    client.delete(f"/favorites/{ids[0]}", headers=auth_headers(token))

    assert favoritar(client, token, 999).status_code == 201


def test_premium_cancelado_volta_a_ter_limite(client, db_session):
    db_session.add(Assinatura(usuario_id=63, premium=False, stripe_subscription_id="sub_cancelada"))
    db_session.commit()
    token = criar_token(usuario_id=63)
    for filme in range(1, LIMITE_FAVORITOS_GRATIS + 1):
        favoritar(client, token, filme)

    assert favoritar(client, token, 999).status_code == 403


def test_perfil_mostra_selo_premium(client, db_session, auth_service):
    tornar_premium(db_session, 64)
    quem_ve = auth_headers(criar_token(usuario_id=65))

    assert client.get("/profiles/64", headers=quem_ve).json()["premium"] is True
    assert client.get("/profiles/65", headers=quem_ve).json()["premium"] is False
