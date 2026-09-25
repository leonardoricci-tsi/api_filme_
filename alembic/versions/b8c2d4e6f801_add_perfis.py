"""add perfis (bio e chave da foto no object storage)

Revision ID: b8c2d4e6f801
Revises: f1a2b3c4d5e6
Create Date: 2026-09-25 00:00:00.000000

Atividade 6: perfil de usuário. `foto_key` guarda só a chave do objeto no
Garage — o arquivo nunca entra no banco.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b8c2d4e6f801'
down_revision: Union[str, None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'perfis',
        sa.Column('usuario_id', sa.Integer(), autoincrement=False, nullable=False),
        sa.Column('bio', sa.String(length=280), nullable=True),
        sa.Column('foto_key', sa.String(length=255), nullable=True),
        sa.Column('atualizado_em', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('usuario_id'),
    )


def downgrade() -> None:
    op.drop_table('perfis')
