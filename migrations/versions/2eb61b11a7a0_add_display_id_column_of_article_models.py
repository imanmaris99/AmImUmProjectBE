"""add display_id column of article models

Revision ID: 2eb61b11a7a0
Revises: ad1c26b7bd74
Create Date: 2024-10-17 15:16:20.642779

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2eb61b11a7a0'
down_revision: Union[str, None] = 'ad1c26b7bd74'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Menambahkan kolom display_id pada tabel articles
    op.add_column('articles', sa.Column('display_id', sa.String(length=50), nullable=True))
    op.create_index(op.f('ix_articles_display_id'), 'articles', ['display_id'], unique=True)

    # ### end Alembic commands ###


def downgrade() -> None:
    # Menghapus kolom display_id pada tabel articles
    op.drop_index(op.f('ix_articles_display_id'), table_name='articles')
    op.drop_column('articles', 'display_id')
    # ### end Alembic commands ###
