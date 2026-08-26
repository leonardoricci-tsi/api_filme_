import itertools

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import get_settings
from app.database import Base, get_db
from app.main import app

_proximo_usuario_id = itertools.count(1)


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


def criar_token(usuario_id: int | None = None, role: str = "usuario") -> str:
    """Gera um JWT do jeito que o auth-service geraria — o catálogo só
    verifica a assinatura localmente, não tem mais tabela de usuários pra
    consultar, então os testes de favoritos/comentários não precisam de um
    usuário "de verdade": só de um token válido com um usuario_id qualquer.
    """
    if usuario_id is None:
        usuario_id = next(_proximo_usuario_id)
    settings = get_settings()
    payload = {"sub": str(usuario_id), "role": role}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
