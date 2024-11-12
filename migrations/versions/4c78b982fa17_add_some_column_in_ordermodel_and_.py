"""add some column in Ordermodel and Orderitemmodel

Revision ID: 4c78b982fa17
Revises: 486bab4dbae7
Create Date: 2024-11-11 05:11:48.174802

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4c78b982fa17'
down_revision: Union[str, None] = '486bab4dbae7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Definisikan enum terlebih dahulu
    delivery_type_enum = sa.Enum('delivery', 'pickup', name='deliverytypeenum')
    delivery_type_enum.create(op.get_bind(), checkfirst=True)

    # Tambahkan kolom di order_items
    op.add_column('order_items', sa.Column('variant_id', sa.Integer(), nullable=True))
    op.add_column('order_items', sa.Column('price_per_item', sa.DECIMAL(precision=10, scale=2), nullable=False))
    op.add_column('order_items', sa.Column('total_price', sa.DECIMAL(precision=10, scale=2), nullable=False))
    op.create_index(op.f('ix_order_items_variant_id'), 'order_items', ['variant_id'], unique=False)
    op.create_foreign_key(None, 'order_items', 'pack_types', ['variant_id'], ['id'])
    op.drop_column('order_items', 'price')

    # Tambahkan kolom di orders menggunakan enum
    op.add_column('orders', sa.Column('delivery_type', delivery_type_enum, nullable=False))
    op.add_column('orders', sa.Column('notes', sa.String(length=100), nullable=True))


def downgrade() -> None:
    # Hapus kolom di orders
    op.drop_column('orders', 'notes')
    op.drop_column('orders', 'delivery_type')

    # Hapus enum setelah kolom dihapus
    delivery_type_enum = sa.Enum('delivery', 'pickup', name='deliverytypeenum')
    delivery_type_enum.drop(op.get_bind(), checkfirst=True)

    # Tambahkan kembali kolom dan constraint di order_items
    op.add_column('order_items', sa.Column('price', sa.NUMERIC(precision=10, scale=2), autoincrement=False, nullable=False))
    op.drop_constraint(None, 'order_items', type_='foreignkey')
    op.drop_index(op.f('ix_order_items_variant_id'), table_name='order_items')
    op.drop_column('order_items', 'total_price')
    op.drop_column('order_items', 'price_per_item')
    op.drop_column('order_items', 'variant_id')
