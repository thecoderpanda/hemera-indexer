"""add_traces_table

Revision ID: 57a618f8d159
Revises: cb718e0fb5c8
Create Date: 2024-05-21 18:35:57.998574

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '57a618f8d159'
down_revision: Union[str, None] = 'cb718e0fb5c8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('traces',
    sa.Column('trace_id', sa.VARCHAR(), nullable=False),
    sa.Column('from_address', postgresql.BYTEA(), nullable=True),
    sa.Column('to_address', postgresql.BYTEA(), nullable=True),
    sa.Column('value', sa.NUMERIC(precision=100), nullable=True),
    sa.Column('input', postgresql.BYTEA(), nullable=True),
    sa.Column('output', postgresql.BYTEA(), nullable=True),
    sa.Column('trace_type', sa.VARCHAR(), nullable=True),
    sa.Column('call_type', sa.VARCHAR(), nullable=True),
    sa.Column('gas', sa.NUMERIC(precision=100), nullable=True),
    sa.Column('gas_used', sa.NUMERIC(precision=100), nullable=True),
    sa.Column('subtraces', sa.INTEGER(), nullable=True),
    sa.Column('trace_address', postgresql.ARRAY(sa.INTEGER()), nullable=True),
    sa.Column('error', sa.TEXT(), nullable=True),
    sa.Column('status', sa.INTEGER(), nullable=True),
    sa.Column('block_number', sa.BIGINT(), nullable=True),
    sa.Column('block_hash', postgresql.BYTEA(), nullable=True),
    sa.Column('block_timestamp', postgresql.TIMESTAMP(), nullable=True),
    sa.Column('transaction_index', sa.INTEGER(), nullable=True),
    sa.Column('transaction_hash', postgresql.BYTEA(), nullable=True),
    sa.Column('create_time', postgresql.TIMESTAMP(), nullable=True),
    sa.Column('update_time', postgresql.TIMESTAMP(), nullable=True),
    sa.PrimaryKeyConstraint('trace_id')
    )
    op.alter_column('logs', 'block_hash',
               existing_type=postgresql.BYTEA(),
               nullable=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('logs', 'block_hash',
               existing_type=postgresql.BYTEA(),
               nullable=False)
    op.drop_table('traces')
    # ### end Alembic commands ###