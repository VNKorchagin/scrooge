"""Add soft delete and admin flag to users

Revision ID: 003
Revises: 002
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add is_active column for soft delete
    op.add_column('users', sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'))
    # Add is_admin column
    op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=True, server_default='false'))
    # Add deleted_at timestamp
    op.add_column('users', sa.Column('deleted_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'deleted_at')
    op.drop_column('users', 'is_admin')
    op.drop_column('users', 'is_active')
