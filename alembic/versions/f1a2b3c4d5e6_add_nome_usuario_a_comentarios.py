"""add nome_usuario a comentarios

Revision ID: f1a2b3c4d5e6
Revises: d7e4a9b1c3f5
Create Date: 2026-08-30 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, None] = 'd7e4a9b1c3f5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('comentarios', sa.Column('nome_usuario', sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column('comentarios', 'nome_usuario')
