import httpx
import respx
from httpx import Response

from app.config import get_settings

AUTH_SERVICE_URL = get_settings().auth_service_url


@respx.mock
def test_register_repassa_resposta_do_auth_service(client):
    respx.post(f"{AUTH_SERVICE_URL}/auth/register").mock(
        return_value=Response(201, json={"access_token": "abc.def.ghi", "token_type": "bearer"})
    )

    resposta = client.post(
        "/auth/register",
        json={"nome": "Ana", "email": "ana@example.com", "senha": "senha12345"},
    )

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["access_token"] == "abc.def.ghi"
    assert corpo["token_type"] == "bearer"


@respx.mock
def test_register_email_duplicado_repassa_400_do_auth_service(client):
    respx.post(f"{AUTH_SERVICE_URL}/auth/register").mock(
        return_value=Response(400, json={"detail": "Email já cadastrado"})
    )

    resposta = client.post(
        "/auth/register",
        json={"nome": "Outro", "email": "dup@example.com", "senha": "outrasenha"},
    )

    assert resposta.status_code == 400
    assert resposta.json()["detail"] == "Email já cadastrado"


@respx.mock
def test_login_repassa_resposta_do_auth_service(client):
    respx.post(f"{AUTH_SERVICE_URL}/auth/login").mock(
        return_value=Response(200, json={"access_token": "xyz.token", "token_type": "bearer"})
    )

    resposta = client.post(
        "/auth/login", json={"email": "login@example.com", "senha": "minhasenha123"}
    )

    assert resposta.status_code == 200
    assert resposta.json()["access_token"] == "xyz.token"


@respx.mock
def test_login_credenciais_invalidas_repassa_401_do_auth_service(client):
    respx.post(f"{AUTH_SERVICE_URL}/auth/login").mock(
        return_value=Response(401, json={"detail": "Email ou senha inválidos"})
    )

    resposta = client.post(
        "/auth/login", json={"email": "login2@example.com", "senha": "senhaerrada"}
    )

    assert resposta.status_code == 401


@respx.mock
def test_me_repassa_authorization_header_pro_auth_service(client):
    rota_mock = respx.get(f"{AUTH_SERVICE_URL}/auth/me").mock(
        return_value=Response(
            200,
            json={
                "id": 1,
                "nome": "Fulano",
                "email": "me@example.com",
                "role": "usuario",
                "criado_em": "2026-01-01T00:00:00",
            },
        )
    )

    resposta = client.get("/auth/me", headers={"Authorization": "Bearer algum-token"})

    assert resposta.status_code == 200
    assert resposta.json()["nome"] == "Fulano"
    assert rota_mock.calls.last.request.headers["Authorization"] == "Bearer algum-token"


@respx.mock
def test_me_sem_token_repassa_401_do_auth_service(client):
    respx.get(f"{AUTH_SERVICE_URL}/auth/me").mock(
        return_value=Response(401, json={"detail": "Credenciais inválidas ou expiradas"})
    )

    resposta = client.get("/auth/me")

    assert resposta.status_code == 401


@respx.mock
def test_auth_service_fora_do_ar_retorna_502(client):
    respx.post(f"{AUTH_SERVICE_URL}/auth/login").mock(
        side_effect=httpx.ConnectError("connection refused")
    )

    resposta = client.post(
        "/auth/login", json={"email": "qualquer@example.com", "senha": "qualquer123"}
    )

    assert resposta.status_code == 502
