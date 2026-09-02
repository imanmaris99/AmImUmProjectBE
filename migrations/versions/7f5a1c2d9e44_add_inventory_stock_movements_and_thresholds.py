"""add inventory stock movements and thresholds

Revision ID: 7f5a1c2d9e44
Revises: 9e7c1a2b3f4d
Create Date: 2026-09-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7f5a1c2d9e44'
down_revision: Union[str, None] = '9e7c1a2b3f4d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'stock_movements',
        sa.Column('id', sa.CHAR(length=36), nullable=False),
        sa.Column('variant_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.CHAR(length=36), nullable=True),
        sa.Column('movement_type', sa.String(length=20), nullable=False),
        sa.Column('delta', sa.Integer(), nullable=False),
        sa.Column('stock_before', sa.Integer(), nullable=True),
        sa.Column('stock_after', sa.Integer(), nullable=True),
        sa.Column('actor_id', sa.CHAR(length=36), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('reference', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['actor_id'], ['users.id']),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
        sa.ForeignKeyConstraint(['variant_id'], ['pack_types.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_stock_movements_id'), 'stock_movements', ['id'], unique=True)
    op.create_index(op.f('ix_stock_movements_variant_id'), 'stock_movements', ['variant_id'], unique=False)
    op.create_index(op.f('ix_stock_movements_product_id'), 'stock_movements', ['product_id'], unique=False)
    op.create_index(op.f('ix_stock_movements_movement_type'), 'stock_movements', ['movement_type'], unique=False)
    op.create_index(op.f('ix_stock_movements_actor_id'), 'stock_movements', ['actor_id'], unique=False)
    op.create_index(op.f('ix_stock_movements_reference'), 'stock_movements', ['reference'], unique=False)
    op.create_index(op.f('ix_stock_movements_created_at'), 'stock_movements', ['created_at'], unique=False)

    op.create_table(
        'inventory_thresholds',
        sa.Column('variant_id', sa.Integer(), nullable=False),
        sa.Column('min_threshold', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('updated_by', sa.CHAR(length=36), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id']),
        sa.ForeignKeyConstraint(['variant_id'], ['pack_types.id']),
        sa.PrimaryKeyConstraint('variant_id'),
    )
    op.create_index(op.f('ix_inventory_thresholds_variant_id'), 'inventory_thresholds', ['variant_id'], unique=False)
    op.create_index(op.f('ix_inventory_thresholds_updated_by'), 'inventory_thresholds', ['updated_by'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_inventory_thresholds_updated_by'), table_name='inventory_thresholds')
    op.drop_index(op.f('ix_inventory_thresholds_variant_id'), table_name='inventory_thresholds')
    op.drop_table('inventory_thresholds')

    op.drop_index(op.f('ix_stock_movements_created_at'), table_name='stock_movements')
    op.drop_index(op.f('ix_stock_movements_reference'), table_name='stock_movements')
    op.drop_index(op.f('ix_stock_movements_actor_id'), table_name='stock_movements')
    op.drop_index(op.f('ix_stock_movements_movement_type'), table_name='stock_movements')
    op.drop_index(op.f('ix_stock_movements_product_id'), table_name='stock_movements')
    op.drop_index(op.f('ix_stock_movements_variant_id'), table_name='stock_movements')
    op.drop_index(op.f('ix_stock_movements_id'), table_name='stock_movements')
    op.drop_table('stock_movements')
