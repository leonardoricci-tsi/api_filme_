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
    # Idem para o log-service (atividade 5) — auditoria de favoritar,
    # comentar, apagar comentário e tentativa negada (403).
    log_service_url: str = "http://log-service:8002"
    # Object storage (atividade 6): Garage, falado via API S3. Dois endereços
    # porque a URL pré-assinada embute o host na assinatura — o catálogo
    # grava/apaga pela rede interna (s3_endpoint_url), mas assina com o
    # endereço que o navegador consegue abrir (s3_public_url).
    s3_endpoint_url: str = "http://garage:3900"
    s3_public_url: str = "http://localhost:3900"
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_bucket: str = "api-filmes-perfis"
    # Tem que bater com o `s3_region` do garage.toml, senão a assinatura falha.
    s3_region: str = "garage"
    s3_url_expira_segundos: int = 900


@lru_cache
def get_settings() -> Settings:
    return Settings()
