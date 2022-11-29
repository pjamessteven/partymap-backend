"""empty message

Revision ID: 45465c516e6e
Revises: a3d9ebe1eb4c
Create Date: 2021-11-30 17:26:57.866453

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '45465c516e6e'
down_revision = 'a3d9ebe1eb4c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('artist_urls',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('artist_id', sa.Integer(), nullable=True),
    sa.Column('url', sa.String(), nullable=True),
    sa.Column('type', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['artist_id'], ['artists.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_column('artists', 'spotify_url')
    op.drop_column('artists', 'bandcamp_url')
    op.drop_column('artists', 'soundcloud_url')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('artists', sa.Column('soundcloud_url', sa.VARCHAR(length=200), autoincrement=False, nullable=True))
    op.add_column('artists', sa.Column('bandcamp_url', sa.VARCHAR(length=200), autoincrement=False, nullable=True))
    op.add_column('artists', sa.Column('spotify_url', sa.VARCHAR(length=200), autoincrement=False, nullable=True))
    op.drop_table('artist_urls')
    # ### end Alembic commands ###
