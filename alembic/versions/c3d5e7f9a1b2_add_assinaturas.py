"""add assinaturas (plano premium via Stripe)

Revision ID: c3d5e7f9a1b2
Revises: b8c2d4e6f801
Create Date: 2026-10-09 00:00:00.000000

Atividade 7: quem é premium. Guarda só os IDs de cliente/assinatura do
Stripe — nenhum dado de cartão (ele nem chega no backend).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d5e7f9a1b2'
down_revision: Union[str, None] = 'b8c2d4e6f801'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'assinaturas',
        sa.Column('usuario_id', sa.Integer(), autoincrement=False, nullable=False),
        sa.Column('premium', sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column('stripe_customer_id', sa.String(length=255), nullable=True),
        sa.Column('stripe_subscription_id', sa.String(length=255), nullable=True),
        sa.Column('atualizado_em', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('usuario_id'),
        sa.UniqueConstraint('stripe_subscription_id'),
    )


def downgrade() -> None:
    op.drop_table('assinaturas')
