"""empty message

Revision ID: c2eaf559118c
Revises: ce4e74083eab
Create Date: 2024-02-28 07:38:19.429744

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c2eaf559118c'
down_revision = 'ce4e74083eab'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('event_date_ticket',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('event_date_id', sa.Integer(), nullable=True),
    sa.Column('url', sa.String(), nullable=True),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('price_min', sa.Integer(), nullable=True),
    sa.Column('price_max', sa.Integer(), nullable=True),
    sa.Column('price_currency_code', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['event_date_id'], ['event_dates.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('event_date_ticket')
    # ### end Alembic commands ###