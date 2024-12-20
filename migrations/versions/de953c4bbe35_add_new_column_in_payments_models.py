"""Add new column in payments models

Revision ID: de953c4bbe35
Revises: 0ca61e43df19
Create Date: 2024-11-25 17:21:17.854799

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'de953c4bbe35'
down_revision: Union[str, None] = '0ca61e43df19'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Nama enum yang akan dibuat
fraud_status_enum = sa.Enum(
    'accept', 'challenge', 'deny', 
    name='fraudstatusenum'
)
transaction_status_enum = sa.Enum(
    'pending', 'settlement', 'expire', 'cancel', 'deny', 'refund',
    name='transactionstatusenum'
)

def upgrade() -> None:
    # Buat tipe enum transactionstatusenum dan fraudstatusenum
    transaction_status_enum.create(op.get_bind(), checkfirst=True)
    fraud_status_enum.create(op.get_bind(), checkfirst=True)

    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        'payments',
        'payment_type',
        existing_type=sa.VARCHAR(length=50),
        nullable=True
    )
    # Ubah tipe kolom transaction_status menjadi enum dengan casting eksplisit
    op.alter_column(
        'payments',
        'transaction_status',
        existing_type=sa.VARCHAR(length=50),
        type_=transaction_status_enum,
        nullable=True,
        postgresql_using="transaction_status::text::transactionstatusenum"
    )

    # Tambahkan kolom fraud_status
    op.add_column(
        'payments',
        sa.Column('fraud_status', fraud_status_enum, nullable=True)
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # Hapus kolom fraud_status
    op.drop_column('payments', 'fraud_status')

    # Kembalikan tipe kolom transaction_status ke VARCHAR
    op.alter_column(
        'payments',
        'transaction_status',
        existing_type=transaction_status_enum,
        type_=sa.VARCHAR(length=50),
        nullable=False
    )

    # Kembalikan payment_type ke nullable=False
    op.alter_column(
        'payments',
        'payment_type',
        existing_type=sa.VARCHAR(length=50),
        nullable=False
    )

    # Hapus tipe enum transactionstatusenum dan fraudstatusenum
    transaction_status_enum.drop(op.get_bind(), checkfirst=True)
    fraud_status_enum.drop(op.get_bind(), checkfirst=True)