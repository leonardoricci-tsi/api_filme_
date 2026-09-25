from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Nome do serviço no docker-compose (rede interna) — sem porta publicada
    # pro host, igual ao restante da comunicação entre os serviços.
    redis_url: str = "redis://redis:6379/0"
    # Mesmo segredo do catálogo e do auth-service: permite decodificar o JWT
    # localmente pra decidir quem é admin, sem round-trip pro auth-service.
    jwt_secret: str
    jwt_algorithm: str = "HS256"


@lru_cache
def get_settings() -> Settings:
    return Settings()
