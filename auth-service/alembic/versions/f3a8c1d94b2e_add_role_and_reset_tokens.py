"""add role a usuarios e cria reset_tokens

Revision ID: f3a8c1d94b2e
Revises:
Create Date: 2026-08-26 00:00:00.000000

Não recria `usuarios` — essa tabela já existe no banco (criada pelo
Alembic do catálogo, revisão 6c7cac7f3161). O auth-service assume posse
dela a partir daqui: só altera (adiciona `role`) e cria o que é novo.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f3a8c1d94b2e'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'usuarios',
        sa.Column('role', sa.String(length=50), nullable=False, server_default='usuario'),
    )
    op.create_table(
        'reset_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('token', sa.String(length=64), nullable=False),
        sa.Column('usuario_id', sa.Integer(), nullable=False),
        sa.Column('criado_em', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('expira_em', sa.DateTime(), nullable=False),
        sa.Column('usado', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.ForeignKeyConstraint(
            ['usuario_id'], ['usuarios.id'], name='fk_reset_tokens_usuario_id', ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_reset_tokens_token'), 'reset_tokens', ['token'], unique=True)
    op.create_index(op.f('ix_reset_tokens_usuario_id'), 'reset_tokens', ['usuario_id'], unique=False)


def downgrade() -> None:
    op.drop_constraint('fk_reset_tokens_usuario_id', 'reset_tokens', type_='foreignkey')
    op.drop_index(op.f('ix_reset_tokens_usuario_id'), table_name='reset_tokens')
    op.drop_index(op.f('ix_reset_tokens_token'), table_name='reset_tokens')
    op.drop_table('reset_tokens')
    op.drop_column('usuarios', 'role')
