from collections.abc import Generator
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


def utc_now_naive() -> datetime:
    """UTC atual sem tzinfo — casa com o tipo DateTime (naive) do MySQL."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


settings = get_settings()

engine = create_engine(
    settings.database_url,
    # Mesmo trade-off do catálogo: sem pool_pre_ping (round-trip extra caro
    # no MySQL remoto), com pool_recycle pra evitar conexão derrubada por
    # firewall/proxy intermediário em conexões ociosas.
    pool_recycle=280,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
