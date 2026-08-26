from datetime import datetime

from sqlalchemy import DateTime, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base, utc_now_naive


class Favorito(Base):
    __tablename__ = "favoritos"
    __table_args__ = (
        UniqueConstraint("usuario_id", "tmdb_movie_id", name="uq_favorito_usuario_filme"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    # Sem ForeignKey pra usuarios: essa tabela é do auth-service agora,
    # outro serviço, outro dono. O usuario_id só é validado pelo JWT — nunca
    # por uma constraint de banco entre os dois serviços.
    usuario_id: Mapped[int] = mapped_column(index=True, nullable=False)
    tmdb_movie_id: Mapped[int] = mapped_column(nullable=False)
    titulo: Mapped[str] = mapped_column(String(500), nullable=False)
    poster_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now_naive, server_default=func.now()
    )
