"""merge heads after product_images

Revision ID: 9e7c1a2b3f4d
Revises: d11525791bbc, f3c9c2f1a7b1
Create Date: 2026-04-30 08:40:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '9e7c1a2b3f4d'
down_revision: Union[str, Sequence[str], None] = ('d11525791bbc', 'f3c9c2f1a7b1')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
