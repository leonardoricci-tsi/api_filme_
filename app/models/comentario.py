from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, utc_now_naive

if TYPE_CHECKING:
    from app.models.usuario import Usuario


class Comentario(Base):
    __tablename__ = "comentarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE", name="fk_comentarios_usuario_id"),
        index=True,
        nullable=False,
    )
    tmdb_movie_id: Mapped[int] = mapped_column(nullable=False, index=True)
    titulo: Mapped[str | None] = mapped_column(String(500), nullable=True)
    poster_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    texto: Mapped[str] = mapped_column(Text, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now_naive, server_default=func.now()
    )

    usuario: Mapped["Usuario"] = relationship(back_populates="comentarios")
