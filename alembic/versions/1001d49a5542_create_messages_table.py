"""create messages table

Revision ID: 1001d49a5542
Revises:
Create Date: 2021-01-10 14:22:43.426073

"""
from alembic import op
import sqlalchemy as sa

from constants import (
    MAX_MESSAGE_LENGTH,
    MESSAGE_SEQ_NAME,
)

# revision identifiers, used by Alembic.
revision = '1001d49a5542'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute(sa.schema.CreateSequence(sa.schema.Sequence(MESSAGE_SEQ_NAME)))
    op.create_table(
        'messages',
        sa.Column(
            'pk_id',
            sa.Integer,
            sa.Sequence(MESSAGE_SEQ_NAME),
            primary_key=True,
        ),
        sa.Column('text', sa.String(MAX_MESSAGE_LENGTH)),
        sa.Column('chat_id', sa.BigInteger, nullable=False),
        sa.Column('ts', sa.BigInteger, nullable=False),
    )


def downgrade():
    op.execute(sa.schema.DropSequence(sa.schema.Sequence(MESSAGE_SEQ_NAME)))
    op.drop_table('messages')
