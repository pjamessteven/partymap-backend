"""empty message

Revision ID: 8f00db9070d1
Revises: c685c063644d
Create Date: 2021-11-22 23:40:37.560453

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8f00db9070d1'
down_revision = 'c685c063644d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('suggested_edits', sa.Column('approved_at', sa.DateTime(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('suggested_edits', 'approved_at')
    # ### end Alembic commands ###
