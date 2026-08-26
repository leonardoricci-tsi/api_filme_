from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base, utc_now_naive


class Comentario(Base):
    __tablename__ = "comentarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Sem ForeignKey pra usuarios: essa tabela é do auth-service agora,
    # outro serviço, outro dono. O usuario_id só é validado pelo JWT — nunca
    # por uma constraint de banco entre os dois serviços.
    usuario_id: Mapped[int] = mapped_column(index=True, nullable=False)
    tmdb_movie_id: Mapped[int] = mapped_column(nullable=False, index=True)
    titulo: Mapped[str | None] = mapped_column(String(500), nullable=True)
    poster_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    texto: Mapped[str] = mapped_column(Text, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now_naive, server_default=func.now()
    )
