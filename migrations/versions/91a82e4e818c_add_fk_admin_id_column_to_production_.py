"""add fk_admin_id column to production & product type model

Revision ID: 91a82e4e818c
Revises: a443cd47ede1
Create Date: 2024-10-20 12:56:03.019716

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '91a82e4e818c'
down_revision: Union[str, None] = 'a443cd47ede1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('pack_types', sa.Column('fk_admin_id', mysql.CHAR(length=36), nullable=True))
    op.create_foreign_key(None, 'pack_types', 'users', ['fk_admin_id'], ['id'])
    op.add_column('productions', sa.Column('fk_admin_id', mysql.CHAR(length=36), nullable=True))
    op.create_foreign_key(None, 'productions', 'users', ['fk_admin_id'], ['id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'productions', type_='foreignkey')
    op.drop_column('productions', 'fk_admin_id')
    op.drop_constraint(None, 'pack_types', type_='foreignkey')
    op.drop_column('pack_types', 'fk_admin_id')
    # ### end Alembic commands ###