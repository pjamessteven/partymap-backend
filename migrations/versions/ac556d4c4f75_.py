"""empty message

Revision ID: ac556d4c4f75
Revises:
Create Date: 2020-08-02 20:04:11.511628

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import geoalchemy2
import sqlalchemy_utils
# revision identifiers, used by Alembic.
revision = 'ac556d4c4f75'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('artists',
                    sa.Column('name', sa.String(length=50), nullable=False),
                    sa.Column('description', sa.Text(), nullable=True),
                    sa.Column('urls', sa.Text(), nullable=True),
                    sa.PrimaryKeyConstraint('name')
                    )
    op.create_table('clusters_10',
                    sa.Column('cluster_id', postgresql.UUID(), nullable=False),
                    sa.Column('count', sa.Integer(), nullable=True),
                    sa.Column('centroid', geoalchemy2.types.Geometry(geometry_type='POINT',
                                                                     from_text='ST_GeomFromEWKT', name='geometry'), nullable=True),
                    sa.PrimaryKeyConstraint('cluster_id')
                    )
    op.create_table('clusters_11',
                    sa.Column('cluster_id', postgresql.UUID(), nullable=False),
                    sa.Column('count', sa.Integer(), nullable=True),
                    sa.Column('centroid', geoalchemy2.types.Geometry(geometry_type='POINT',
                                                                     from_text='ST_GeomFromEWKT', name='geometry'), nullable=True),
                    sa.PrimaryKeyConstraint('cluster_id')
                    )
    op.create_table('clusters_12',
                    sa.Column('cluster_id', postgresql.UUID(), nullable=False),
                    sa.Column('count', sa.Integer(), nullable=True),
                    sa.Column('centroid', geoalchemy2.types.Geometry(geometry_type='POINT',
                                                                     from_text='ST_GeomFromEWKT', name='geometry'), nullable=True),
                    sa.PrimaryKeyConstraint('cluster_id')
                    )
    op.create_table('clusters_13',
                    sa.Column('cluster_id', postgresql.UUID(), nullable=False),
                    sa.Column('count', sa.Integer(), nullable=True),
                    sa.Column('centroid', geoalchemy2.types.Geometry(geometry_type='POINT',
                                                                     from_text='ST_GeomFromEWKT', name='geometry'), nullable=True),
                    sa.PrimaryKeyConstraint('cluster_id')
                    )
    op.create_table('clusters_14',
                    sa.Column('cluster_id', postgresql.UUID(), nullable=False),
                    sa.Column('count', sa.Integer(), nullable=True),
                    sa.Column('centroid', geoalchemy2.types.Geometry(geometry_type='POINT',
                                                                     from_text='ST_GeomFromEWKT', name='geometry'), nullable=True),
                    sa.PrimaryKeyConstraint('cluster_id')
                    )
    op.create_table('clusters_15',
                    sa.Column('cluster_id', postgresql.UUID(), nullable=False),
                    sa.Column('count', sa.Integer(), nullable=True),
                    sa.Column('centroid', geoalchemy2.types.Geometry(geometry_type='POINT',
                                                                     from_text='ST_GeomFromEWKT', name='geometry'), nullable=True),
                    sa.PrimaryKeyConstraint('cluster_id')
                    )
    op.create_table('clusters_16',
                    sa.Column('cluster_id', postgresql.UUID(), nullable=False),
                    sa.Column('count', sa.Integer(), nullable=True),
                    sa.Column('centroid', geoalchemy2.types.Geometry(geometry_type='POINT',
                                                                     from_text='ST_GeomFromEWKT', name='geometry'), nullable=True),
                    sa.PrimaryKeyConstraint('cluster_id')
                    )
    op.create_table('clusters_2',
                    sa.Column('cluster_id', postgresql.UUID(), nullable=False),
                    sa.Column('count', sa.Integer(), nullable=True),
                    sa.Column('centroid', geoalchemy2.types.Geometry(geometry_type='POINT',
                                                                     from_text='ST_GeomFromEWKT', name='geometry'), nullable=True),
                    sa.PrimaryKeyConstraint('cluster_id')
                    )
    op.create_table('clusters_3',
                    sa.Column('cluster_id', postgresql.UUID(), nullable=False),
                    sa.Column('count', sa.Integer(), nullable=True),
                    sa.Column('centroid', geoalchemy2.types.Geometry(geometry_type='POINT',
                                                                     from_text='ST_GeomFromEWKT', name='geometry'), nullable=True),
                    sa.PrimaryKeyConstraint('cluster_id')
                    )
    op.create_table('clusters_4',
                    sa.Column('cluster_id', postgresql.UUID(), nullable=False),
                    sa.Column('count', sa.Integer(), nullable=True),
                    sa.Column('centroid', geoalchemy2.types.Geometry(geometry_type='POINT',
                                                                     from_text='ST_GeomFromEWKT', name='geometry'), nullable=True),
                    sa.PrimaryKeyConstraint('cluster_id')
                    )
    op.create_table('clusters_5',
                    sa.Column('cluster_id', postgresql.UUID(), nullable=False),
                    sa.Column('count', sa.Integer(), nullable=True),
                    sa.Column('centroid', geoalchemy2.types.Geometry(geometry_type='POINT',
                                                                     from_text='ST_GeomFromEWKT', name='geometry'), nullable=True),
                    sa.PrimaryKeyConstraint('cluster_id')
                    )
    op.create_table('clusters_6',
                    sa.Column('cluster_id', postgresql.UUID(), nullable=False),
                    sa.Column('count', sa.Integer(), nullable=True),
                    sa.Column('centroid', geoalchemy2.types.Geometry(geometry_type='POINT',
                                                                     from_text='ST_GeomFromEWKT', name='geometry'), nullable=True),
                    sa.PrimaryKeyConstraint('cluster_id')
                    )
    op.create_table('clusters_7',
                    sa.Column('cluster_id', postgresql.UUID(), nullable=False),
                    sa.Column('count', sa.Integer(), nullable=True),
                    sa.Column('centroid', geoalchemy2.types.Geometry(geometry_type='POINT',
                                                                     from_text='ST_GeomFromEWKT', name='geometry'), nullable=True),
                    sa.PrimaryKeyConstraint('cluster_id')
                    )
    op.create_table('clusters_8',
                    sa.Column('cluster_id', postgresql.UUID(), nullable=False),
                    sa.Column('count', sa.Integer(), nullable=True),
                    sa.Column('centroid', geoalchemy2.types.Geometry(geometry_type='POINT',
                                                                     from_text='ST_GeomFromEWKT', name='geometry'), nullable=True),
                    sa.PrimaryKeyConstraint('cluster_id')
                    )
    op.create_table('clusters_9',
                    sa.Column('cluster_id', postgresql.UUID(), nullable=False),
                    sa.Column('count', sa.Integer(), nullable=True),
                    sa.Column('centroid', geoalchemy2.types.Geometry(geometry_type='POINT',
                                                                     from_text='ST_GeomFromEWKT', name='geometry'), nullable=True),
                    sa.PrimaryKeyConstraint('cluster_id')
                    )
    op.create_table('event_location_types',
                    sa.Column('type', sa.String(), nullable=False),
                    sa.PrimaryKeyConstraint('type')
                    )
    op.create_table('tags',
                    sa.Column('tag', sa.String(length=20), nullable=False),
                    sa.Column('created', sa.DateTime(), nullable=True),
                    sa.PrimaryKeyConstraint('tag')
                    )
    op.create_table('users',
                    sa.Column('id', postgresql.UUID(), nullable=False),
                    sa.Column('created', sa.DateTime(timezone=True), nullable=False),
                    sa.Column('modified', sa.DateTime(timezone=True), nullable=False),
                    sa.Column('last_active', sa.DateTime(), nullable=True),
                    sa.Column('username', sa.String(length=80), nullable=True),
                    sa.Column('email', sa.String(length=120), nullable=False),
                    sa.Column('password', sa.String(length=255), nullable=True),
                    sa.Column('oauth', sa.Boolean(), nullable=True),
                    sa.Column('karma', sa.Integer(), nullable=True),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('email'),
                    sa.UniqueConstraint('username')
                    )
    op.create_table('event_locations',
                    sa.Column('place_id', sa.String(), nullable=False),
                    sa.Column('geohash', sa.String(), nullable=True),
                    sa.Column('geo', geoalchemy2.types.Geometry(geometry_type='POINT',
                                                                from_text='ST_GeomFromEWKT', name='geometry'), nullable=True),
                    sa.Column('name', sa.String(), nullable=True),
                    sa.Column('description', sa.String(), nullable=True),
                    sa.Column('lat', sa.Float(), nullable=True),
                    sa.Column('lng', sa.Float(), nullable=True),
                    sa.Column('country_code', sa.String(), nullable=True),
                    sa.Column('city', sa.String(), nullable=True),
                    sa.Column('creator_id', postgresql.UUID(), nullable=True),
                    sa.Column('cluster_zoom_2_id', postgresql.UUID(), nullable=True),
                    sa.Column('cluster_zoom_3_id', postgresql.UUID(), nullable=True),
                    sa.Column('cluster_zoom_4_id', postgresql.UUID(), nullable=True),
                    sa.Column('cluster_zoom_5_id', postgresql.UUID(), nullable=True),
                    sa.Column('cluster_zoom_6_id', postgresql.UUID(), nullable=True),
                    sa.Column('cluster_zoom_7_id', postgresql.UUID(), nullable=True),
                    sa.Column('cluster_zoom_8_id', postgresql.UUID(), nullable=True),
                    sa.Column('cluster_zoom_9_id', postgresql.UUID(), nullable=True),
                    sa.Column('cluster_zoom_10_id', postgresql.UUID(), nullable=True),
                    sa.Column('cluster_zoom_11_id', postgresql.UUID(), nullable=True),
                    sa.Column('cluster_zoom_12_id', postgresql.UUID(), nullable=True),
                    sa.Column('cluster_zoom_13_id', postgresql.UUID(), nullable=True),
                    sa.Column('cluster_zoom_14_id', postgresql.UUID(), nullable=True),
                    sa.Column('cluster_zoom_15_id', postgresql.UUID(), nullable=True),
                    sa.Column('cluster_zoom_16_id', postgresql.UUID(), nullable=True),
                    sa.ForeignKeyConstraint(['cluster_zoom_10_id'], [
                                            'clusters_10.cluster_id'], ),
                    sa.ForeignKeyConstraint(['cluster_zoom_11_id'], [
                                            'clusters_11.cluster_id'], ),
                    sa.ForeignKeyConstraint(['cluster_zoom_12_id'], [
                                            'clusters_12.cluster_id'], ),
                    sa.ForeignKeyConstraint(['cluster_zoom_13_id'], [
                                            'clusters_13.cluster_id'], ),
                    sa.ForeignKeyConstraint(['cluster_zoom_14_id'], [
                                            'clusters_14.cluster_id'], ),
                    sa.ForeignKeyConstraint(['cluster_zoom_15_id'], [
                                            'clusters_15.cluster_id'], ),
                    sa.ForeignKeyConstraint(['cluster_zoom_16_id'], [
                                            'clusters_16.cluster_id'], ),
                    sa.ForeignKeyConstraint(['cluster_zoom_2_id'], [
                                            'clusters_2.cluster_id'], ),
                    sa.ForeignKeyConstraint(['cluster_zoom_3_id'], [
                                            'clusters_3.cluster_id'], ),
                    sa.ForeignKeyConstraint(['cluster_zoom_4_id'], [
                                            'clusters_4.cluster_id'], ),
                    sa.ForeignKeyConstraint(['cluster_zoom_5_id'], [
                                            'clusters_5.cluster_id'], ),
                    sa.ForeignKeyConstraint(['cluster_zoom_6_id'], [
                                            'clusters_6.cluster_id'], ),
                    sa.ForeignKeyConstraint(['cluster_zoom_7_id'], [
                                            'clusters_7.cluster_id'], ),
                    sa.ForeignKeyConstraint(['cluster_zoom_8_id'], [
                                            'clusters_8.cluster_id'], ),
                    sa.ForeignKeyConstraint(['cluster_zoom_9_id'], [
                                            'clusters_9.cluster_id'], ),
                    sa.ForeignKeyConstraint(['creator_id'], ['users.id'], ),
                    sa.PrimaryKeyConstraint('place_id')
                    )
    op.create_table('flask_dance_oauth',
                    sa.Column('created', sa.DateTime(timezone=True), nullable=False),
                    sa.Column('modified', sa.DateTime(timezone=True), nullable=False),
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('provider', sa.String(length=50), nullable=False),
                    sa.Column('created_at', sa.DateTime(), nullable=False),
                    sa.Column('token', sqlalchemy_utils.types.json.JSONType(),
                              nullable=False),
                    sa.Column('provider_user_id', sa.String(length=256), nullable=False),
                    sa.Column('user_id', postgresql.UUID(), nullable=True),
                    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('provider_user_id')
                    )
    op.create_table('notifications',
                    sa.Column('id', postgresql.UUID(), nullable=False),
                    sa.Column('created', sa.DateTime(timezone=True), nullable=False),
                    sa.Column('modified', sa.DateTime(timezone=True), nullable=False),
                    sa.Column('user_id', postgresql.UUID(), nullable=True),
                    sa.Column('notification_type', sa.String(), nullable=True),
                    sa.Column('notification_url', sa.String(), nullable=True),
                    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('user_notifications',
                    sa.Column('id', postgresql.UUID(), nullable=False),
                    sa.Column('created', sa.DateTime(timezone=True), nullable=False),
                    sa.Column('modified', sa.DateTime(timezone=True), nullable=False),
                    sa.Column('user_id', postgresql.UUID(), nullable=False),
                    sa.Column('read', sa.Boolean(), nullable=True),
                    sa.ForeignKeyConstraint(
                        ['user_id'], ['users.id'], ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('id', 'user_id')
                    )
    op.create_table('event_location_type_association',
                    sa.Column('type', sa.String(), nullable=True),
                    sa.Column('place_id', sa.String(), nullable=True),
                    sa.ForeignKeyConstraint(['place_id'], ['event_locations.place_id'], ),
                    sa.ForeignKeyConstraint(['type'], ['event_location_types.type'], )
                    )
    op.create_table('events',
                    sa.Column('id', postgresql.UUID(), nullable=False),
                    sa.Column('created', sa.DateTime(timezone=True), nullable=False),
                    sa.Column('modified', sa.DateTime(timezone=True), nullable=False),
                    sa.Column('creator_id', postgresql.UUID(), nullable=True),
                    sa.Column('owner_id', postgresql.UUID(), nullable=True),
                    sa.Column('name', sa.Text(), nullable=False),
                    sa.Column('description', sa.Text(), nullable=True),
                    sa.Column('default_url', sa.String(), nullable=True),
                    sa.Column('default_location_place_id', sa.String(), nullable=True),
                    sa.Column('settings', postgresql.JSONB(
                        astext_type=sa.Text()), nullable=True),
                    sa.ForeignKeyConstraint(['creator_id'], ['users.id'], ),
                    sa.ForeignKeyConstraint(['default_location_place_id'], [
                        'event_locations.place_id'], ),
                    sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('event_dates',
                    sa.Column('id', postgresql.UUID(), nullable=False),
                    sa.Column('created', sa.DateTime(timezone=True), nullable=False),
                    sa.Column('modified', sa.DateTime(timezone=True), nullable=False),
                    sa.Column('creator_id', postgresql.UUID(), nullable=True),
                    sa.Column('event_id', postgresql.UUID(), nullable=True),
                    sa.Column('tz', sa.String(), nullable=False),
                    sa.Column('event_start', sa.DateTime(), nullable=False),
                    sa.Column('event_start_naive', sa.DateTime(), nullable=False),
                    sa.Column('event_end', sa.DateTime(), nullable=True),
                    sa.Column('event_end_naive', sa.DateTime(), nullable=True),
                    sa.Column('all_day', sa.Boolean(), nullable=False),
                    sa.Column('location_id', sa.String(), nullable=True),
                    sa.Column('description', sa.Text(), nullable=True),
                    sa.Column('url', sa.String(), nullable=True),
                    sa.Column('cancelled', sa.Boolean(), nullable=True),
                    sa.ForeignKeyConstraint(['creator_id'], ['users.id'], ),
                    sa.ForeignKeyConstraint(['event_id'], ['events.id'], ),
                    sa.ForeignKeyConstraint(
                        ['location_id'], ['event_locations.place_id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('event_owners',
                    sa.Column('event_id', postgresql.UUID(), nullable=True),
                    sa.Column('user_id', postgresql.UUID(), nullable=True),
                    sa.ForeignKeyConstraint(['event_id'], ['events.id'], ),
                    sa.ForeignKeyConstraint(['user_id'], ['users.id'], )
                    )
    op.create_table('event_tag_downvotes',
                    sa.Column('user_id', postgresql.UUID(), nullable=False),
                    sa.Column('tag', sa.String(length=20), nullable=False),
                    sa.Column('event_id', postgresql.UUID(), nullable=False),
                    sa.ForeignKeyConstraint(['event_id'], ['events.id'], ),
                    sa.ForeignKeyConstraint(['tag'], ['tags.tag'], ),
                    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
                    sa.PrimaryKeyConstraint('user_id', 'tag', 'event_id')
                    )
    op.create_table('event_tag_upvotes',
                    sa.Column('user_id', postgresql.UUID(), nullable=False),
                    sa.Column('tag', sa.String(length=20), nullable=False),
                    sa.Column('event_id', postgresql.UUID(), nullable=False),
                    sa.ForeignKeyConstraint(['event_id'], ['events.id'], ),
                    sa.ForeignKeyConstraint(['tag'], ['tags.tag'], ),
                    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
                    sa.PrimaryKeyConstraint('user_id', 'tag', 'event_id')
                    )
    op.create_table('event_tags',
                    sa.Column('tag_id', sa.String(length=20), nullable=False),
                    sa.Column('event_id', postgresql.UUID(), nullable=False),
                    sa.Column('creator_id', postgresql.UUID(), nullable=True),
                    sa.Column('created', sa.DateTime(), nullable=True),
                    sa.Column('status', sa.SmallInteger(), nullable=True),
                    sa.Column('votes', sa.Integer(), nullable=True),
                    sa.Column('hotness', sa.Float(
                        precision=15, asdecimal=6), nullable=True),
                    sa.ForeignKeyConstraint(['creator_id'], ['users.id'], ),
                    sa.ForeignKeyConstraint(['event_id'], ['events.id'], ),
                    sa.ForeignKeyConstraint(['tag_id'], ['tags.tag'], ),
                    sa.PrimaryKeyConstraint('tag_id', 'event_id')
                    )
    op.create_table('favorites_association',
                    sa.Column('user', postgresql.UUID(), nullable=True),
                    sa.Column('event', postgresql.UUID(), nullable=True),
                    sa.ForeignKeyConstraint(['event'], ['events.id'], ),
                    sa.ForeignKeyConstraint(['user'], ['users.id'], )
                    )
    op.create_table('rrules',
                    sa.Column('event_id', postgresql.UUID(), nullable=False),
                    sa.Column('recurring_type', sa.Integer(), nullable=False),
                    sa.Column('separation_count', sa.Integer(), nullable=True),
                    sa.Column('day_of_week', sa.Integer(), nullable=True),
                    sa.Column('week_of_month', sa.Integer(), nullable=True),
                    sa.Column('day_of_month', sa.Integer(), nullable=True),
                    sa.Column('month_of_year', sa.Integer(), nullable=True),
                    sa.ForeignKeyConstraint(['event_id'], ['events.id'], ),
                    sa.PrimaryKeyConstraint('event_id')
                    )
    op.create_table('event_artist_downvotes',
                    sa.Column('user_id', postgresql.UUID(), nullable=False),
                    sa.Column('artist_name', sa.String(), nullable=False),
                    sa.Column('event_date_id', postgresql.UUID(), nullable=False),
                    sa.ForeignKeyConstraint(['artist_name'], ['artists.name'], ),
                    sa.ForeignKeyConstraint(['event_date_id'], ['event_dates.id'], ),
                    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
                    sa.PrimaryKeyConstraint('user_id', 'artist_name', 'event_date_id')
                    )
    op.create_table('event_artist_upvotes',
                    sa.Column('user_id', postgresql.UUID(), nullable=False),
                    sa.Column('artist_name', sa.String(), nullable=False),
                    sa.Column('event_date_id', postgresql.UUID(), nullable=False),
                    sa.ForeignKeyConstraint(['artist_name'], ['artists.name'], ),
                    sa.ForeignKeyConstraint(['event_date_id'], ['event_dates.id'], ),
                    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
                    sa.PrimaryKeyConstraint('user_id', 'artist_name', 'event_date_id')
                    )
    op.create_table('event_artists',
                    sa.Column('artist_name', sa.String(length=50), nullable=False),
                    sa.Column('event_date_id', postgresql.UUID(), nullable=False),
                    sa.Column('creator_id', postgresql.UUID(), nullable=True),
                    sa.Column('status', sa.SmallInteger(), nullable=True),
                    sa.Column('votes', sa.Integer(), nullable=True),
                    sa.Column('hotness', sa.Float(
                        precision=15, asdecimal=6), nullable=True),
                    sa.ForeignKeyConstraint(['artist_name'], ['artists.name'], ),
                    sa.ForeignKeyConstraint(['creator_id'], ['users.id'], ),
                    sa.ForeignKeyConstraint(['event_date_id'], ['event_dates.id'], ),
                    sa.PrimaryKeyConstraint('artist_name', 'event_date_id')
                    )
    op.create_table('event_contributions',
                    sa.Column('id', postgresql.UUID(), nullable=False),
                    sa.Column('created', sa.DateTime(timezone=True), nullable=False),
                    sa.Column('modified', sa.DateTime(timezone=True), nullable=False),
                    sa.Column('text', sa.Text(), nullable=True),
                    sa.Column('creator_id', postgresql.UUID(), nullable=False),
                    sa.Column('event_id', postgresql.UUID(), nullable=False),
                    sa.Column('event_date_id', postgresql.UUID(), nullable=True),
                    sa.Column('status', sa.SmallInteger(), nullable=True),
                    sa.Column('score', sa.Integer(), nullable=True),
                    sa.Column('hotness', sa.Float(
                        precision=15, asdecimal=6), nullable=True),
                    sa.ForeignKeyConstraint(['creator_id'], ['users.id'], ),
                    sa.ForeignKeyConstraint(['event_date_id'], ['event_dates.id'], ),
                    sa.ForeignKeyConstraint(['event_id'], ['events.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('event_contribution_downvotes',
                    sa.Column('user_id', postgresql.UUID(), nullable=True),
                    sa.Column('event_contribution_id', postgresql.UUID(), nullable=True),
                    sa.ForeignKeyConstraint(['event_contribution_id'], [
                                            'event_contributions.id'], ),
                    sa.ForeignKeyConstraint(['user_id'], ['users.id'], )
                    )
    op.create_table('event_contribution_upvotes',
                    sa.Column('user_id', postgresql.UUID(), nullable=True),
                    sa.Column('event_contribution_id', postgresql.UUID(), nullable=True),
                    sa.ForeignKeyConstraint(['event_contribution_id'], [
                                            'event_contributions.id'], ),
                    sa.ForeignKeyConstraint(['user_id'], ['users.id'], )
                    )
    op.create_table('event_images',
                    sa.Column('id', postgresql.UUID(), nullable=False),
                    sa.Column('created', sa.DateTime(timezone=True), nullable=False),
                    sa.Column('modified', sa.DateTime(timezone=True), nullable=False),
                    sa.Column('filename', sa.String(), nullable=False),
                    sa.Column('thumb_filename', sa.String(), nullable=False),
                    sa.Column('caption', sa.Text(), nullable=True),
                    sa.Column('creator_id', postgresql.UUID(), nullable=True),
                    sa.Column('contribution_id', postgresql.UUID(), nullable=True),
                    sa.Column('event_id', postgresql.UUID(), nullable=True),
                    sa.Column('status', sa.SmallInteger(), nullable=True),
                    sa.Column('score', sa.Integer(), nullable=True),
                    sa.Column('hotness', sa.Float(
                        precision=15, asdecimal=6), nullable=True),
                    sa.ForeignKeyConstraint(['contribution_id'], [
                                            'event_contributions.id'], ),
                    sa.ForeignKeyConstraint(['creator_id'], ['users.id'], ),
                    sa.ForeignKeyConstraint(['event_id'], ['events.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('event_image_downvotes',
                    sa.Column('user_id', postgresql.UUID(), nullable=True),
                    sa.Column('event_image_id', postgresql.UUID(), nullable=True),
                    sa.ForeignKeyConstraint(['event_image_id'], ['event_images.id'], ),
                    sa.ForeignKeyConstraint(['user_id'], ['users.id'], )
                    )
    op.create_table('event_image_upvotes',
                    sa.Column('user_id', postgresql.UUID(), nullable=True),
                    sa.Column('event_image_id', postgresql.UUID(), nullable=True),
                    sa.ForeignKeyConstraint(['event_image_id'], ['event_images.id'], ),
                    sa.ForeignKeyConstraint(['user_id'], ['users.id'], )
                    )
    op.create_table('reports',
                    sa.Column('id', postgresql.UUID(), nullable=False),
                    sa.Column('created', sa.DateTime(timezone=True), nullable=False),
                    sa.Column('modified', sa.DateTime(timezone=True), nullable=False),
                    sa.Column('creator_id', postgresql.UUID(), nullable=False),
                    sa.Column('creator_ip', sa.String(length=50), nullable=True),
                    sa.Column('reason_text', sa.Text(), nullable=True),
                    sa.Column('user_id', postgresql.UUID(), nullable=False),
                    sa.Column('event_id', postgresql.UUID(), nullable=True),
                    sa.Column('event_date_id', postgresql.UUID(), nullable=True),
                    sa.Column('event_contribution_id', postgresql.UUID(), nullable=True),
                    sa.Column('event_image_id', postgresql.UUID(), nullable=True),
                    sa.Column('event_artist_artist_name', sa.String(), nullable=True),
                    sa.Column('event_tag_tag_id', sa.String(), nullable=True),
                    sa.ForeignKeyConstraint(['creator_id'], ['users.id'], ),
                    sa.ForeignKeyConstraint(['event_contribution_id'], [
                                            'event_contributions.id'], ),
                    sa.ForeignKeyConstraint(['event_date_id', 'event_artist_artist_name'], [
                        'event_artists.event_date_id', 'event_artists.artist_name'], ),
                    sa.ForeignKeyConstraint(['event_date_id'], ['event_dates.id'], ),
                    sa.ForeignKeyConstraint(['event_id', 'event_tag_tag_id'], [
                        'event_tags.event_id', 'event_tags.tag_id'], ),
                    sa.ForeignKeyConstraint(['event_id'], ['events.id'], ),
                    sa.ForeignKeyConstraint(['event_image_id'], ['event_images.id'], ),
                    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('spatial_ref_sys',
                    sa.Column('srid', sa.INTEGER(), autoincrement=False, nullable=False),
                    sa.Column('auth_name', sa.VARCHAR(length=256),
                              autoincrement=False, nullable=True),
                    sa.Column('auth_srid', sa.INTEGER(),
                              autoincrement=False, nullable=True),
                    sa.Column('srtext', sa.VARCHAR(length=2048),
                              autoincrement=False, nullable=True),
                    sa.Column('proj4text', sa.VARCHAR(length=2048),
                              autoincrement=False, nullable=True),
                    sa.CheckConstraint('(srid > 0) AND (srid <= 998999)',
                                       name='spatial_ref_sys_srid_check'),
                    sa.PrimaryKeyConstraint('srid', name='spatial_ref_sys_pkey')
                    )
    op.drop_table('reports')
    op.drop_table('event_image_upvotes')
    op.drop_table('event_image_downvotes')
    op.drop_table('event_images')
    op.drop_table('event_contribution_upvotes')
    op.drop_table('event_contribution_downvotes')
    op.drop_table('event_contributions')
    op.drop_table('event_artists')
    op.drop_table('event_artist_upvotes')
    op.drop_table('event_artist_downvotes')
    op.drop_table('rrules')
    op.drop_table('favorites_association')
    op.drop_table('event_tags')
    op.drop_table('event_tag_upvotes')
    op.drop_table('event_tag_downvotes')
    op.drop_table('event_owners')
    op.drop_table('event_dates')
    op.drop_table('events')
    op.drop_table('event_location_type_association')
    op.drop_table('user_notifications')
    op.drop_table('notifications')
    op.drop_table('flask_dance_oauth')
    op.drop_table('event_locations')
    op.drop_table('users')
    op.drop_table('tags')
    op.drop_table('event_location_types')
    op.drop_table('clusters_9')
    op.drop_table('clusters_8')
    op.drop_table('clusters_7')
    op.drop_table('clusters_6')
    op.drop_table('clusters_5')
    op.drop_table('clusters_4')
    op.drop_table('clusters_3')
    op.drop_table('clusters_2')
    op.drop_table('clusters_16')
    op.drop_table('clusters_15')
    op.drop_table('clusters_14')
    op.drop_table('clusters_13')
    op.drop_table('clusters_12')
    op.drop_table('clusters_11')
    op.drop_table('clusters_10')
    op.drop_table('artists')
    # ### end Alembic commands ###
