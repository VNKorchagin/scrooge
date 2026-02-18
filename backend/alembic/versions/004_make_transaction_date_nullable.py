"""Make transaction_date nullable

Revision ID: 004
Revises: 003
Create Date: 2024-02-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Make transaction_date nullable
    op.alter_column('transactions', 'transaction_date',
                    existing_type=sa.DateTime(),
                    nullable=True)


def downgrade() -> None:
    # Make transaction_date non-nullable again
    op.alter_column('transactions', 'transaction_date',
                    existing_type=sa.DateTime(),
                    nullable=False)
