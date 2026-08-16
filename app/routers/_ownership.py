from fastapi import HTTPException, status
from sqlalchemy.orm import Session


def get_owned_or_404(db: Session, model, resource_id: int, usuario_id: int):
    """Busca um recurso garantindo que pertence ao usuário logado.

    Sempre filtra por usuario_id na própria query (nunca busca por id e checa
    depois), e retorna 404 — não 403 — quando o recurso não existe ou é de
    outro usuário, para não vazar a existência dele.
    """
    obj = (
        db.query(model)
        .filter(model.id == resource_id, model.usuario_id == usuario_id)
        .first()
    )
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recurso não encontrado")
    return obj
