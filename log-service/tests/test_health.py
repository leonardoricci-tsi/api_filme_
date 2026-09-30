from redis.exceptions import ConnectionError as RedisConnectionError


def test_liveness_sempre_responde(client):
    resposta = client.get("/health/live")

    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok"}


def test_redis_no_ar_da_200(client):
    resposta = client.get("/health")

    assert resposta.status_code == 200
    assert resposta.json()["status"] == "ok"
    assert resposta.json()["checagens"]["redis"]["status"] == "ok"


def test_redis_fora_da_503(client, fake_redis):
    """É esse 503 que faz o HEALTHCHECK do Docker marcar o log-service como
    unhealthy quando o Redis cai — sem ninguém tocar no container."""

    def redis_fora():
        raise RedisConnectionError("Error 111 connecting to redis:6379. Connection refused.")

    fake_redis.ping = redis_fora

    resposta = client.get("/health")

    assert resposta.status_code == 503
    corpo = resposta.json()
    assert corpo["status"] == "fail"
    assert corpo["checagens"]["redis"] == {
        "status": "fail",
        "erro": "ConnectionError",
        "critica": True,
        "ms": corpo["checagens"]["redis"]["ms"],
    }
