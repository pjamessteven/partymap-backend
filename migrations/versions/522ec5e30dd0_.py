"""empty message

Revision ID: 522ec5e30dd0
Revises: dc4a2252f424
Create Date: 2024-10-29 00:12:25.934197

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '522ec5e30dd0'
down_revision = 'dc4a2252f424'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('event_dates', sa.Column('description_translations', postgresql.HSTORE(text_type=sa.Text()), nullable=True))
    op.add_column('event_dates_version', sa.Column('description_translations', postgresql.HSTORE(text_type=sa.Text()), autoincrement=False, nullable=True))
    op.add_column('event_reviews', sa.Column('text_translations', postgresql.HSTORE(text_type=sa.Text()), nullable=True))
    op.add_column('event_reviews_version', sa.Column('text_translations', postgresql.HSTORE(text_type=sa.Text()), autoincrement=False, nullable=True))
    op.add_column('events', sa.Column('description_translations', postgresql.HSTORE(text_type=sa.Text()), nullable=True))
    op.add_column('events', sa.Column('full_description_translations', postgresql.HSTORE(text_type=sa.Text()), nullable=True))
    op.add_column('events', sa.Column('name_translations', postgresql.HSTORE(text_type=sa.Text()), nullable=True))
    op.add_column('events_version', sa.Column('description_translations', postgresql.HSTORE(text_type=sa.Text()), autoincrement=False, nullable=True))
    op.add_column('events_version', sa.Column('full_description_translations', postgresql.HSTORE(text_type=sa.Text()), autoincrement=False, nullable=True))
    op.add_column('events_version', sa.Column('name_translations', postgresql.HSTORE(text_type=sa.Text()), autoincrement=False, nullable=True))
    op.add_column('feedbacks', sa.Column('fk_feedbacks_creator_id', postgresql.UUID(), nullable=True))
    op.drop_constraint('feedbacks_creator_id_fkey', 'feedbacks', type_='foreignkey')
    op.create_foreign_key(None, 'feedbacks', 'users', ['fk_feedbacks_creator_id'], ['id'])
    op.drop_column('feedbacks', 'creator_id')
    op.add_column('users', sa.Column('locale', sa.String(length=16), nullable=True))
    # ### end Alembic commands ###

    # Migrate data to new translaction dicts
    connection = op.get_bind()
    
    # Event dates
    results = connection.execute(sa.text("SELECT id, description FROM event_dates")).fetchall()
    
    for row in results:
        connection.execute(
            sa.text("UPDATE event_dates SET description_translations = :translations WHERE id = :id"),
            {"translations": {"en": row.description}, "id": row.id}
        )

    # Event
    results = connection.execute(sa.text("SELECT id, description, full_description, name FROM events")).fetchall()
    
    for row in results:
        connection.execute(
            sa.text("UPDATE events SET name_translations = :translations WHERE id = :id"),
            {"translations": {"en": row.name}, "id": row.id}
        )
        connection.execute(
            sa.text("UPDATE events SET description_translations = :translations WHERE id = :id"),
            {"translations": {"en": row.description}, "id": row.id}
        )
        connection.execute(
            sa.text("UPDATE events SET full_description_translations = :translations WHERE id = :id"),
            {"translations": {"en": row.full_description}, "id": row.id}
        )
    
    # Event reviews
    results = connection.execute(sa.text("SELECT id, text FROM event_reviews")).fetchall()
    
    for row in results:
        connection.execute(
            sa.text("UPDATE event_reviews SET text_translations = :translations WHERE id = :id"),
            {"translations": {"en": row.text}, "id": row.id}
        )



def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'locale')
    op.add_column('feedbacks', sa.Column('creator_id', postgresql.UUID(), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'feedbacks', type_='foreignkey')
    op.create_foreign_key('feedbacks_creator_id_fkey', 'feedbacks', 'users', ['creator_id'], ['id'])
    op.drop_column('feedbacks', 'fk_feedbacks_creator_id')
    op.drop_column('events_version', 'name_translations')
    op.drop_column('events_version', 'full_description_translations')
    op.drop_column('events_version', 'description_translations')
    op.drop_column('events', 'name_translations')
    op.drop_column('events', 'full_description_translations')
    op.drop_column('events', 'description_translations')
    op.drop_column('event_reviews_version', 'text_translations')
    op.drop_column('event_reviews', 'text_translations')
    op.drop_column('event_dates_version', 'description_translations')
    op.drop_column('event_dates', 'description_translations')
    # ### end Alembic commands ###
