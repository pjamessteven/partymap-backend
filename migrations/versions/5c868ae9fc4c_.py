"""empty message

Revision ID: 5c868ae9fc4c
Revises: 95bfec51215e
Create Date: 2021-12-30 18:19:47.837844

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5c868ae9fc4c'
down_revision = '95bfec51215e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('events', sa.Column('rrule_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'events', 'rrules', ['rrule_id'], ['id'])
    op.add_column('events_version', sa.Column('rrule_id', sa.Integer(), autoincrement=False, nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('events_version', 'rrule_id')
    op.drop_constraint(None, 'events', type_='foreignkey')
    op.drop_column('events', 'rrule_id')
    # ### end Alembic commands ###
