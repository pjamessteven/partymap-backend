"""empty message

Revision ID: 68193b370df1
Revises: 3abde8f1ffcb
Create Date: 2021-12-14 18:36:57.297923

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '68193b370df1'
down_revision = '3abde8f1ffcb'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('rrules', sa.Column('event_id', sa.Integer(), nullable=False))
    op.drop_constraint('rrules_id_fkey', 'rrules', type_='foreignkey')
    op.create_foreign_key(None, 'rrules', 'events', ['event_id'], ['id'])
    op.add_column('rrules_version', sa.Column('event_id', sa.Integer(), autoincrement=False, nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('rrules_version', 'event_id')
    op.drop_constraint(None, 'rrules', type_='foreignkey')
    op.create_foreign_key('rrules_id_fkey', 'rrules', 'events', ['id'], ['id'])
    op.drop_column('rrules', 'event_id')
    # ### end Alembic commands ###
