"""add event embeddings

Revision ID: 4c2d5c7f9f01
Revises: f6653e8a7777, 14e83424094d, 2d09fb096713, f65313fd5aed
Create Date: 2026-04-22 12:00:00.000000

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '4c2d5c7f9f01'
down_revision = ('f6653e8a7777', '14e83424094d', '2d09fb096713', 'f65313fd5aed')
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute(
        "ALTER TABLE events ADD COLUMN IF NOT EXISTS search_embedding vector(1536)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_events_search_embedding "
        "ON events USING ivfflat (search_embedding vector_cosine_ops) WITH (lists = 100)"
    )


def downgrade():
    op.execute("DROP INDEX IF EXISTS idx_events_search_embedding")
    op.execute("ALTER TABLE events DROP COLUMN IF EXISTS search_embedding")
