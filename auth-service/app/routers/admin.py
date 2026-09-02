from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_admin
from app.database import get_db
from app.models import Usuario
from app.models.usuario import PAPEIS_VALIDOS
from app.schemas.auth import RoleUpdateIn, UsuarioOut

router = APIRouter(prefix="/auth/admin", tags=["admin"])


@router.get("/users", response_model=list[UsuarioOut])
def listar_usuarios(
    _admin: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[UsuarioOut]:
    """Só admin: lista todos os usuários cadastrados — é o que permite a
    ação exclusiva de admin desta atividade (promover/rebaixar o papel de
    alguém, olhando essa lista pra decidir quem)."""
    return db.query(Usuario).order_by(Usuario.id).all()


@router.patch("/users/{usuario_id}/role", response_model=UsuarioOut)
def alterar_papel_usuario(
    usuario_id: int,
    dados: RoleUpdateIn,
    _admin: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
) -> UsuarioOut:
    """Só admin: promove ou rebaixa o papel de qualquer usuário. Essa é a
    ação exclusiva de admin de verdade — recusa com 403 quem não for
    admin, mesmo chamando o endpoint direto (dependência require_admin)."""
    if dados.role not in PAPEIS_VALIDOS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Papel inválido. Use um de: {', '.join(PAPEIS_VALIDOS)}",
        )

    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")

    usuario.role = dados.role
    db.commit()
    db.refresh(usuario)
    return usuario
