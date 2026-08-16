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
    # Sem pool_pre_ping: cada round-trip até o MySQL remoto custa
    # ~500-700ms, e o pre_ping faz um round-trip extra em TODO checkout de
    # conexão. Em troca, recicla conexões proativamente antes que algum
    # firewall/proxy intermediário as derrube por ociosidade.
    pool_recycle=280,
)
# expire_on_commit=False evita que o SQLAlchemy dispare um SELECT extra
# (round-trip) toda vez que um atributo é lido logo após o commit — cada
# round-trip até o MySQL remoto custa ~300ms, então isso importa bastante.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
