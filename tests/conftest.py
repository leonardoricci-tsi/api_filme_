import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth.dependencies import clear_usuario_cache
from app.database import Base, get_db
from app.main import app


@pytest.fixture(autouse=True)
def _limpar_cache_usuario():
    # Cada teste usa um SQLite em memória novo, então os IDs de usuário
    # reiniciam do 1 — sem isso, o cache de get_current_user vazaria dados
    # de um teste pro outro.
    clear_usuario_cache()
    yield
    clear_usuario_cache()


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def registrar_usuario(client, nome="Usuário Teste", email="teste@example.com", senha="senha12345"):
    resposta = client.post(
        "/auth/register", json={"nome": nome, "email": email, "senha": senha}
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()["access_token"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
