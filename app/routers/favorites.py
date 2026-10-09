from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.dependencies import UsuarioAutenticado, require_papel_minimo
from app.database import get_db
from app.models import Favorito
from app.openapi_responses import (
    RESP_401,
    RESP_403_LIMITE_FAVORITOS,
    RESP_404,
    RESP_409_FAVORITO,
    resp_403_papel,
)
from app.routers._ownership import get_owned_or_404
from app.routers.premium import LIMITE_FAVORITOS_GRATIS, eh_premium
from app.schemas.favorite import FavoriteIn, FavoriteOut
from app.services import log_client

router = APIRouter(prefix="/favorites", tags=["favorites"])

_RESP_NERD = RESP_401 | resp_403_papel("nerd")


@router.post(
    "",
    response_model=FavoriteOut,
    status_code=status.HTTP_201_CREATED,
    responses=_RESP_NERD | RESP_403_LIMITE_FAVORITOS | RESP_409_FAVORITO,
)
def criar_favorito(
    dados: FavoriteIn,
    request: Request,
    usuario_atual: UsuarioAutenticado = Depends(require_papel_minimo("nerd")),
    db: Session = Depends(get_db),
) -> FavoriteOut:
    """O benefício do plano premium (atividade 7) mora aqui: quem não é
    premium para em LIMITE_FAVORITOS_GRATIS, premium não tem limite. Quem é
    premium vem da tabela `assinaturas` (gravada só pelo webhook do
    Stripe) — nunca de nada que o cliente mande na requisição."""
    if not eh_premium(db, usuario_atual.id):
        total = db.query(Favorito).filter(Favorito.usuario_id == usuario_atual.id).count()
        if total >= LIMITE_FAVORITOS_GRATIS:
            log_client.registrar_evento(
                usuario_atual.id,
                "acesso_negado:limite_favoritos",
                ip=request.client.host if request.client else None,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Limite de {LIMITE_FAVORITOS_GRATIS} favoritos do plano gratuito atingido. "
                "Assine o plano Cinéfilo para favoritos ilimitados",
            )
    favorito = Favorito(
        usuario_id=usuario_atual.id,
        tmdb_movie_id=dados.tmdb_movie_id,
        titulo=dados.titulo,
        poster_path=dados.poster_path,
    )
    db.add(favorito)
    try:
        db.commit()
    except IntegrityError as erro:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Filme já favoritado"
        ) from erro
    # Evento mínimo exigido pela atividade 5.
    log_client.registrar_evento(
        usuario_atual.id,
        f"favoritar_filme:{dados.tmdb_movie_id}",
        ip=request.client.host if request.client else None,
    )
    return favorito


@router.get("", response_model=list[FavoriteOut], responses=_RESP_NERD)
def listar_favoritos(
    usuario_atual: UsuarioAutenticado = Depends(require_papel_minimo("nerd")),
    db: Session = Depends(get_db),
) -> list[FavoriteOut]:
    return (
        db.query(Favorito)
        .filter(Favorito.usuario_id == usuario_atual.id)
        .order_by(Favorito.criado_em.desc())
        .all()
    )


@router.delete(
    "/{favorito_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=_RESP_NERD | RESP_404,
)
def deletar_favorito(
    favorito_id: int,
    usuario_atual: UsuarioAutenticado = Depends(require_papel_minimo("nerd")),
    db: Session = Depends(get_db),
) -> None:
    favorito = get_owned_or_404(db, Favorito, favorito_id, usuario_atual.id)
    db.delete(favorito)
    db.commit()
