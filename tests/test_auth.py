from tests.conftest import auth_headers, registrar_usuario


def test_register_cria_usuario_e_retorna_token(client):
    resposta = client.post(
        "/auth/register",
        json={"nome": "Ana", "email": "ana@example.com", "senha": "senha12345"},
    )
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert "access_token" in corpo
    assert corpo["token_type"] == "bearer"


def test_register_email_duplicado_retorna_400(client):
    registrar_usuario(client, email="dup@example.com")
    resposta = client.post(
        "/auth/register",
        json={"nome": "Outro", "email": "dup@example.com", "senha": "outrasenha"},
    )
    assert resposta.status_code == 400


def test_login_com_senha_correta_retorna_token(client):
    registrar_usuario(client, email="login@example.com", senha="minhasenha123")
    resposta = client.post(
        "/auth/login", json={"email": "login@example.com", "senha": "minhasenha123"}
    )
    assert resposta.status_code == 200
    assert "access_token" in resposta.json()


def test_login_com_senha_errada_retorna_401(client):
    registrar_usuario(client, email="login2@example.com", senha="minhasenha123")
    resposta = client.post(
        "/auth/login", json={"email": "login2@example.com", "senha": "senhaerrada"}
    )
    assert resposta.status_code == 401


def test_login_email_inexistente_retorna_401(client):
    resposta = client.post(
        "/auth/login", json={"email": "naoexiste@example.com", "senha": "qualquer123"}
    )
    assert resposta.status_code == 401


def test_me_retorna_dados_do_usuario_logado(client):
    token = registrar_usuario(client, nome="Fulano", email="me@example.com")

    resposta = client.get("/auth/me", headers=auth_headers(token))

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["nome"] == "Fulano"
    assert corpo["email"] == "me@example.com"


def test_me_sem_token_retorna_401(client):
    resposta = client.get("/auth/me")
    assert resposta.status_code == 401
