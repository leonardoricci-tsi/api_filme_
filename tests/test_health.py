import pytest
import respx
from httpx import Response
from sqlalchemy.exc import OperationalError

from app.config import get_settings
from app.database import get_db
from app.main import app
from app.services import storage


@pytest.fixture()
def dependencias_ok(monkeypatch):
    """auth-service e log-service vivos, Garage com o bucket — o MySQL é o
    SQLite em memória do conftest."""
    settings = get_settings()
    monkeypatch.setattr(storage, "verificar_bucket", lambda: None)
    with respx.mock(assert_all_called=False) as mock:
        mock.get(f"{settings.auth_service_url}/health/live").mock(return_value=Response(200))
        mock.get(f"{settings.log_service_url}/health/live").mock(return_value=Response(200))
        yield mock


def test_liveness_sempre_responde(client):
    resposta = client.get("/health/live")

    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok"}


def test_tudo_no_ar_da_200_ok(client, dependencias_ok):
    resposta = client.get("/health")

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["status"] == "ok"
    assert {nome: c["status"] for nome, c in corpo["checagens"].items()} == {
        "mysql": "ok",
        "auth-service": "ok",
        "log-service": "ok",
        "garage": "ok",
    }


def test_mysql_fora_da_503(client, dependencias_ok):
    """O /health que sempre dá 200 é o erro que a atividade cobra: com o
    banco fora, o catálogo NÃO está pronto e tem que dizer isso."""

    class SessaoSemBanco:
        def execute(self, *_):
            raise OperationalError("SELECT 1", {}, Exception("Can't connect to MySQL server"))

    app.dependency_overrides[get_db] = lambda: SessaoSemBanco()

    resposta = client.get("/health")

    assert resposta.status_code == 503
    corpo = resposta.json()
    assert corpo["status"] == "fail"
    assert corpo["checagens"]["mysql"]["status"] == "fail"
    assert corpo["checagens"]["mysql"]["erro"] == "OperationalError"


def test_garage_fora_deixa_degraded_mas_200(client, dependencias_ok, monkeypatch):
    def garage_fora():
        raise storage.StorageUnavailable("fora")

    monkeypatch.setattr(storage, "verificar_bucket", garage_fora)

    resposta = client.get("/health")

    assert resposta.status_code == 200
    assert resposta.json()["status"] == "degraded"
    assert resposta.json()["checagens"]["garage"]["status"] == "fail"


def test_servicos_internos_fora_deixam_degraded_mas_200(client, monkeypatch):
    """Sem mock pro auth-service/log-service: o conftest aponta os dois pra
    uma porta local fechada, então a conexão é recusada de verdade."""
    monkeypatch.setattr(storage, "verificar_bucket", lambda: None)

    resposta = client.get("/health")

    assert resposta.status_code == 200
    checagens = resposta.json()["checagens"]
    assert resposta.json()["status"] == "degraded"
    assert checagens["auth-service"]["status"] == "fail"
    assert checagens["log-service"]["status"] == "fail"
    assert checagens["mysql"]["status"] == "ok"


def test_health_nao_exige_login(client, dependencias_ok):
    """O Docker/Prometheus chamam sem token — health atrás de login seria inútil."""
    assert client.get("/health").status_code == 200
