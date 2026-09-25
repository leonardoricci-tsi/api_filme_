import os

import jwt
import pytest
from fakeredis import FakeRedis
from fastapi.testclient import TestClient

os.environ.setdefault("JWT_SECRET", "segredo-de-teste")

from app.config import get_settings  # noqa: E402
from app.main import app  # noqa: E402
from app.redis_client import get_redis  # noqa: E402

settings = get_settings()


@pytest.fixture()
def fake_redis():
    return FakeRedis(decode_responses=True)


@pytest.fixture()
def client(fake_redis):
    app.dependency_overrides[get_redis] = lambda: fake_redis
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def token_para(usuario_id: int, role: str) -> str:
    return jwt.encode({"sub": str(usuario_id), "role": role}, settings.jwt_secret, algorithm=settings.jwt_algorithm)
