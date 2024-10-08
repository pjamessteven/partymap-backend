"""empty message

Revision ID: 69f0f7f1a22b
Revises: 7b6adc205de6
Create Date: 2021-12-14 18:15:45.112133

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '69f0f7f1a22b'
down_revision = '7b6adc205de6'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('rrules', sa.Column('end_date_time', sa.String(), nullable=True))
    op.add_column('rrules', sa.Column('start_date_time', sa.String(), nullable=True))
    op.drop_column('rrules', 'time')
    op.add_column('rrules_version', sa.Column('end_date_time', sa.String(), autoincrement=False, nullable=True))
    op.add_column('rrules_version', sa.Column('start_date_time', sa.String(), autoincrement=False, nullable=True))
    op.drop_column('rrules_version', 'time')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('rrules_version', sa.Column('time', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.drop_column('rrules_version', 'start_date_time')
    op.drop_column('rrules_version', 'end_date_time')
    op.add_column('rrules', sa.Column('time', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.drop_column('rrules', 'start_date_time')
    op.drop_column('rrules', 'end_date_time')
    # ### end Alembic commands ###
