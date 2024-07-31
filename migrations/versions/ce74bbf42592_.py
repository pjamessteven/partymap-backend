"""empty message

Revision ID: ce74bbf42592
Revises: 9635c2b756bb
Create Date: 2024-07-30 10:16:57.947880

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ce74bbf42592'
down_revision = '9635c2b756bb'
branch_labels = None
depends_on = None


def upgrade():
    # Step 1: Clear the table
    op.execute('DELETE FROM event_contributions')
    op.drop_table('event_contribution_upvotes')
    op.drop_table('event_contribution_downvotes')
    # Step 2: Drop the existing UUID primary key column
    op.drop_column('media_items', 'contribution_id')

    op.drop_column('event_contributions', 'id', cascase=True)

    # Step 3: Add a new integer primary key column
    op.add_column('event_contributions', sa.Column('id', sa.Integer, primary_key=True, autoincrement=True))

    pass


def downgrade():
    pass
