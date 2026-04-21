"""add price and constraints to pack types

Revision ID: b2f8c1f6a1d2
Revises: 60463190e15f
Create Date: 2026-04-21 11:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


# revision identifiers, used by Alembic.
revision: str = 'b2f8c1f6a1d2'
down_revision: Union[str, None] = '60463190e15f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('pack_types', sa.Column('price', sa.DECIMAL(10, 2), nullable=True))
    op.execute('UPDATE pack_types AS pt SET price = p.price FROM products AS p WHERE p.id = pt.product_id AND pt.price IS NULL')
    op.alter_column('pack_types', 'price', existing_type=sa.DECIMAL(10, 2), nullable=False)
    op.alter_column('pack_types', 'product_id', existing_type=mysql.CHAR(length=36), nullable=False)


def downgrade() -> None:
    op.alter_column('pack_types', 'product_id', existing_type=mysql.CHAR(length=36), nullable=True)
    op.drop_column('pack_types', 'price')
