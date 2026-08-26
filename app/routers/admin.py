from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import UsuarioAutenticado, require_admin
from app.database import get_db
from app.models import Comentario
from app.schemas.comment import CommentOut

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/comments", response_model=list[CommentOut])
def listar_todos_comentarios(
    usuario_atual: UsuarioAutenticado = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[CommentOut]:
    """Só admin: lista comentários de TODOS os usuários (moderação), não só
    os do chamador — diferença de autorização que o `role` do JWT decide."""
    return db.query(Comentario).order_by(Comentario.criado_em.desc()).all()


@router.delete("/comments/{comentario_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_comentario_de_qualquer_usuario(
    comentario_id: int,
    usuario_atual: UsuarioAutenticado = Depends(require_admin),
    db: Session = Depends(get_db),
) -> None:
    """Só admin: remove o comentário de QUALQUER usuário, sem checar
    ownership — ao contrário de DELETE /comments/{id}, que só apaga o
    próprio."""
    comentario = db.get(Comentario, comentario_id)
    if comentario is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recurso não encontrado")
    db.delete(comentario)
    db.commit()
