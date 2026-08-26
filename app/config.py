from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    tmdb_api_key: str
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    # Nome do serviço no docker-compose (rede interna) — o catálogo nunca
    # fala com o auth-service pelo host nem por IP, só por esse DNS interno.
    auth_service_url: str = "http://auth-service:8001"


@lru_cache
def get_settings() -> Settings:
    return Settings()
