from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.auth.dependencies import UsuarioAutenticado, bearer_scheme, get_current_user
from app.database import get_db
from app.models import Favorito, Perfil
from app.openapi_responses import (
    RESP_401,
    RESP_403_PERFIL_ALHEIO,
    RESP_404_USUARIO,
    RESP_502_AUTH_SERVICE,
)
from app.schemas.profile import PerfilOut, PerfilUpdateIn
from app.services import log_client, storage
from app.services.auth_client import AuthServiceUnavailable, forward

router = APIRouter(prefix="/profiles", tags=["profiles"])


def require_dono_do_perfil(
    usuario_id: int,
    request: Request,
    usuario_atual: UsuarioAutenticado = Depends(get_current_user),
) -> UsuarioAutenticado:
    """Só o dono edita o próprio perfil (atividade 6, reaproveitando a
    atividade 4): compara o `usuario_id` da URL com o `sub` do JWT — nunca
    com nada que venha no corpo. Nem admin passa: moderar comentário é
    uma coisa, reescrever a bio de alguém é outra.

    A tentativa negada vai pro log de auditoria (atividade 5), igual às
    negações de `require_admin`/`require_papel_minimo`."""
    if usuario_id != usuario_atual.id:
        log_client.registrar_evento(
            usuario_atual.id,
            f"acesso_negado:perfil:{usuario_id}",
            ip=request.client.host if request.client else None,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Você só pode editar o próprio perfil"
        )
    return usuario_atual


def _buscar_nome(usuario_id: int, credentials: HTTPAuthorizationCredentials | None) -> str:
    """O nome mora na tabela `usuarios`, do auth-service — o catálogo só
    tem bio/foto. Repassa o mesmo token de quem está vendo o perfil."""
    headers = {"Authorization": f"Bearer {credentials.credentials}"} if credentials else {}
    try:
        resposta = forward("GET", f"/auth/users/{usuario_id}", headers=headers)
    except AuthServiceUnavailable as erro:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(erro)) from erro
    if resposta.status_code == status.HTTP_404_NOT_FOUND:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
    if resposta.status_code != status.HTTP_200_OK:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Serviço de autenticação indisponível no momento",
        )
    return resposta.json()["nome"]


def _montar_perfil(
    usuario_id: int,
    usuario_atual: UsuarioAutenticado,
    credentials: HTTPAuthorizationCredentials | None,
    db: Session,
) -> PerfilOut:
    nome = _buscar_nome(usuario_id, credentials)
    # Quem nunca editou o perfil não tem linha em `perfis` — mostra vazio,
    # não 404: o usuário existe (o auth-service acabou de confirmar).
    perfil = db.get(Perfil, usuario_id)
    favoritos = (
        db.query(Favorito)
        .filter(Favorito.usuario_id == usuario_id)
        .order_by(Favorito.criado_em.desc())
        .all()
    )
    foto_key = perfil.foto_key if perfil else None
    return PerfilOut(
        usuario_id=usuario_id,
        nome=nome,
        bio=(perfil.bio if perfil else None) or "",
        foto_url=storage.gerar_url_temporaria(foto_key) if foto_key else None,
        eh_meu=usuario_id == usuario_atual.id,
        favoritos=favoritos,
    )


@router.get(
    "/{usuario_id}",
    response_model=PerfilOut,
    responses=RESP_401 | RESP_404_USUARIO | RESP_502_AUTH_SERVICE,
)
def ver_perfil(
    usuario_id: int,
    usuario_atual: UsuarioAutenticado = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> PerfilOut:
    """Qualquer usuário logado vê o perfil de qualquer outro — é rede
    social. Editar é que é só do dono (PATCH abaixo)."""
    return _montar_perfil(usuario_id, usuario_atual, credentials, db)


@router.patch(
    "/{usuario_id}",
    response_model=PerfilOut,
    responses=RESP_401 | RESP_403_PERFIL_ALHEIO | RESP_404_USUARIO | RESP_502_AUTH_SERVICE,
)
def editar_perfil(
    usuario_id: int,
    dados: PerfilUpdateIn,
    request: Request,
    usuario_atual: UsuarioAutenticado = Depends(require_dono_do_perfil),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> PerfilOut:
    perfil = db.get(Perfil, usuario_atual.id)
    if perfil is None:
        perfil = Perfil(usuario_id=usuario_atual.id)
        db.add(perfil)
    perfil.bio = dados.bio
    db.commit()
    log_client.registrar_evento(
        usuario_atual.id,
        "atualizar_perfil",
        ip=request.client.host if request.client else None,
    )
    return _montar_perfil(usuario_atual.id, usuario_atual, credentials, db)
