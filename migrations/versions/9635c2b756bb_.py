"""empty message

Revision ID: 9635c2b756bb
Revises: 00be8cc1fb1b
Create Date: 2024-07-24 04:16:24.475960

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '9635c2b756bb'
down_revision = '00be8cc1fb1b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('event_contributions_version',
    sa.Column('id', postgresql.UUID(), autoincrement=False, nullable=False),
    sa.Column('created_at', sa.DateTime(), autoincrement=False, nullable=True),
    sa.Column('creator_id', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('event_id', sa.Integer(), autoincrement=False, nullable=True),
    sa.Column('event_date_id', sa.Integer(), autoincrement=False, nullable=True),
    sa.Column('rating', sa.Integer(), autoincrement=False, nullable=True),
    sa.Column('text', sa.Text(), autoincrement=False, nullable=True),
    sa.Column('status', sa.SmallInteger(), autoincrement=False, nullable=True),
    sa.Column('score', sa.Integer(), autoincrement=False, nullable=True),
    sa.Column('hotness', sa.Float(precision=15, asdecimal=6), autoincrement=False, nullable=True),
    sa.Column('transaction_id', sa.BigInteger(), autoincrement=False, nullable=False),
    sa.Column('end_transaction_id', sa.BigInteger(), nullable=True),
    sa.Column('operation_type', sa.SmallInteger(), nullable=False),
    sa.PrimaryKeyConstraint('id', 'transaction_id')
    )
    op.create_index(op.f('ix_event_contributions_version_end_transaction_id'), 'event_contributions_version', ['end_transaction_id'], unique=False)
    op.create_index(op.f('ix_event_contributions_version_operation_type'), 'event_contributions_version', ['operation_type'], unique=False)
    op.create_index(op.f('ix_event_contributions_version_transaction_id'), 'event_contributions_version', ['transaction_id'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_event_contributions_version_transaction_id'), table_name='event_contributions_version')
    op.drop_index(op.f('ix_event_contributions_version_operation_type'), table_name='event_contributions_version')
    op.drop_index(op.f('ix_event_contributions_version_end_transaction_id'), table_name='event_contributions_version')
    op.drop_table('event_contributions_version')
    # ### end Alembic commands ###
