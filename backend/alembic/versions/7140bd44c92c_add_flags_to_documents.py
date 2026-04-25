"""add flags to documents

Revision ID: 7140bd44c92c
Revises: 9772f58b4cd4
Create Date: 2026-04-25 22:11:37.806660

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '7140bd44c92c'
down_revision: Union[str, Sequence[str], None] = '9772f58b4cd4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('chat_messages', sa.Column('sources', sa.JSON(), nullable=True))
    op.add_column('documents', sa.Column('flags', sa.JSON(), nullable=True))
    op.drop_column('documents', 'flagged_keywords')


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column('documents', sa.Column('flagged_keywords', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True))
    op.drop_column('documents', 'flags')
    op.drop_column('chat_messages', 'sources')
