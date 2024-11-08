"""add exception recorder table

Revision ID: 040e5251f45d
Revises: 9a1e927f02bb
Create Date: 2024-08-02 17:57:31.418456

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "040e5251f45d"
down_revision: Union[str, None] = "9a1e927f02bb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "exception_records",
        sa.Column("id", sa.BIGINT(), autoincrement=True, nullable=False),
        sa.Column("block_number", sa.BIGINT(), nullable=True),
        sa.Column("dataclass", sa.VARCHAR(), nullable=True),
        sa.Column("level", sa.VARCHAR(), nullable=True),
        sa.Column("message_type", sa.VARCHAR(), nullable=True),
        sa.Column("message", sa.VARCHAR(), nullable=True),
        sa.Column("exception_env", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("record_time", postgresql.TIMESTAMP(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("exception_records")
    # ### end Alembic commands ###
