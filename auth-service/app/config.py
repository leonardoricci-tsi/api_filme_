from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    jwt_secret: str
    jwt_expire_minutes: int = 60
    jwt_algorithm: str = "HS256"
    # URL pública do catálogo — é ele o único ponto de entrada de fora, então
    # o link de redefinição de senha aponta pra lá (não pro auth-service,
    # que não tem porta publicada).
    catalog_public_url: str = "http://localhost:8000"
    # SMTP de dev (Mailtrap) — em produção essas mesmas variáveis apontariam
    # pro Brevo, sem mudar nenhuma linha de código, só o .env.
    smtp_host: str = "sandbox.smtp.mailtrap.io"
    smtp_port: int = 587
    smtp_user: str
    smtp_password: str
    smtp_from_email: str = "no-reply@catalogo-filmes.local"
    smtp_from_name: str = "Catálogo de Filmes"


@lru_cache
def get_settings() -> Settings:
    return Settings()
