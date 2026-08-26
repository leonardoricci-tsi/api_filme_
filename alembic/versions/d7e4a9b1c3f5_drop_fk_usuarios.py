"""remove FK de favoritos/comentarios pra usuarios

Revision ID: d7e4a9b1c3f5
Revises: 9286b70fe465
Create Date: 2026-08-27 00:00:00.000000

`usuarios` passou a ser dono e mantida pelo auth-service (outro serviço,
outro deploy). O catálogo não pode mais ter uma FK de banco apontando pra
uma tabela que ele não gerencia — a validação de usuario_id passa a ser
só via JWT. O índice em usuario_id continua (ainda é usado nas queries),
só a constraint de integridade referencial é removida.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'd7e4a9b1c3f5'
down_revision: Union[str, None] = '9286b70fe465'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint('fk_favoritos_usuario_id', 'favoritos', type_='foreignkey')
    op.drop_constraint('fk_comentarios_usuario_id', 'comentarios', type_='foreignkey')


def downgrade() -> None:
    op.create_foreign_key(
        'fk_comentarios_usuario_id', 'comentarios', 'usuarios',
        ['usuario_id'], ['id'], ondelete='CASCADE',
    )
    op.create_foreign_key(
        'fk_favoritos_usuario_id', 'favoritos', 'usuarios',
        ['usuario_id'], ['id'], ondelete='CASCADE',
    )
