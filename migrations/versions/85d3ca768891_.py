"""empty message

Revision ID: 85d3ca768891
Revises: 96dc1162c5e1
Create Date: 2021-12-21 12:04:39.053206

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '85d3ca768891'
down_revision = '96dc1162c5e1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('artists_version',
    sa.Column('id', sa.Integer(), autoincrement=False, nullable=False),
    sa.Column('mbid', sa.String(length=100), autoincrement=False, nullable=True),
    sa.Column('name', sa.String(length=50), autoincrement=False, nullable=True),
    sa.Column('created_at', sa.DateTime(), autoincrement=False, nullable=True),
    sa.Column('description', sa.Text(), autoincrement=False, nullable=True),
    sa.Column('disambiguation', sa.Text(), autoincrement=False, nullable=True),
    sa.Column('area', sa.Text(), autoincrement=False, nullable=True),
    sa.Column('transaction_id', sa.BigInteger(), autoincrement=False, nullable=False),
    sa.Column('end_transaction_id', sa.BigInteger(), nullable=True),
    sa.Column('operation_type', sa.SmallInteger(), nullable=False),
    sa.PrimaryKeyConstraint('id', 'transaction_id')
    )
    op.create_index(op.f('ix_artists_version_end_transaction_id'), 'artists_version', ['end_transaction_id'], unique=False)
    op.create_index(op.f('ix_artists_version_operation_type'), 'artists_version', ['operation_type'], unique=False)
    op.create_index(op.f('ix_artists_version_transaction_id'), 'artists_version', ['transaction_id'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_artists_version_transaction_id'), table_name='artists_version')
    op.drop_index(op.f('ix_artists_version_operation_type'), table_name='artists_version')
    op.drop_index(op.f('ix_artists_version_end_transaction_id'), table_name='artists_version')
    op.drop_table('artists_version')
    # ### end Alembic commands ###
