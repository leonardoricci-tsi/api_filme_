from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, utc_now_naive

if TYPE_CHECKING:
    from app.models.comentario import Comentario
    from app.models.favorito import Favorito


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now_naive, server_default=func.now()
    )

    favoritos: Mapped[list["Favorito"]] = relationship(
        back_populates="usuario", cascade="all, delete-orphan"
    )
    comentarios: Mapped[list["Comentario"]] = relationship(
        back_populates="usuario", cascade="all, delete-orphan"
    )
