"""merge alembic heads after pack type price migration

Revision ID: d11525791bbc
Revises: 56ff2a7bd06f, b2f8c1f6a1d2
Create Date: 2026-04-21 20:11:17.946306

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd11525791bbc'
down_revision: Union[str, None] = ('56ff2a7bd06f', 'b2f8c1f6a1d2')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
