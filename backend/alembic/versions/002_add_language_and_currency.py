"""Add language and currency to users

Revision ID: 002
Revises: 001
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add language column
    op.add_column('users', sa.Column('language', sa.String(length=10), nullable=True, server_default='en'))
    # Add currency column
    op.add_column('users', sa.Column('currency', sa.String(length=10), nullable=True, server_default='USD'))


def downgrade() -> None:
    op.drop_column('users', 'currency')
    op.drop_column('users', 'language')
