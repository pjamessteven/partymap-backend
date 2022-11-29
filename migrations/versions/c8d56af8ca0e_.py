"""empty message

Revision ID: c8d56af8ca0e
Revises: 85d3ca768891
Create Date: 2021-12-23 11:50:00.957654

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c8d56af8ca0e'
down_revision = '85d3ca768891'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('event_dates', sa.Column('description_attribute', sa.Text(), nullable=True))
    op.add_column('event_dates_version', sa.Column('description_attribute', sa.Text(), autoincrement=False, nullable=True))
    op.add_column('events', sa.Column('description_attribute', sa.Text(), nullable=True))
    op.add_column('events_version', sa.Column('description_attribute', sa.Text(), autoincrement=False, nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('events_version', 'description_attribute')
    op.drop_column('events', 'description_attribute')
    op.drop_column('event_dates_version', 'description_attribute')
    op.drop_column('event_dates', 'description_attribute')
    # ### end Alembic commands ###
