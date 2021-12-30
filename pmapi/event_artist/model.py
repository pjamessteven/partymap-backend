from datetime import datetime
from sqlalchemy.ext.orderinglist import ordering_list
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import and_, join
from sqlalchemy import select, func

from pmapi.extensions import db
from pmapi.event_date.model import EventDate


class Artist(db.Model):
    __tablename__ = "artists"
    __versioned__ = {}
    id = db.Column(db.Integer, primary_key=True)
    mbid = db.Column(db.String(100))
    name = db.Column(db.String(50), nullable=False)
    events_with_artist = db.relationship("EventDateArtist", back_populates="artist")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    suggestions = db.relationship("SuggestedEdit", back_populates="artist")
    artist_tags = db.relationship("ArtistTag", back_populates="artist")

    # artist specific stuff
    description = db.Column(db.Text)
    disambiguation = db.Column(db.Text)
    area = db.Column(db.Text)
    urls = db.relationship("ArtistUrl")
    media_items = db.relationship(
        "MediaItem",
        back_populates="artist",
        order_by="MediaItem.position",
        collection_class=ordering_list("position"),
    )

    @property
    def event_dates(self):
        now = datetime.utcnow()
        eds = db.session.query(EventDate).join(EventDateArtist)
        eds = eds.filter(
            and_(EventDate.start >= now, EventDateArtist.artist_id == self.id)
        )
        eds = eds.order_by(EventDate.start_naive.asc())
        return eds.all()

    @hybrid_property
    def event_count(self):

        query = (
            db.session.query(EventDateArtist)
            .join(EventDate)
            .filter(
                and_(
                    EventDateArtist.artist_id == self.id,
                    EventDate.start > datetime.utcnow(),
                )
            )
        )
        return query.count()

    @event_count.expression
    def event_count(cls):
        j = join(EventDateArtist, EventDate)
        return (
            select([func.count(EventDateArtist.id)])
            .where(
                and_(
                    EventDateArtist.artist_id == cls.id,
                    EventDate.start > datetime.utcnow(),
                )
            )
            .select_from(j)
        )


class ArtistUrl(db.Model):
    __tablename__ = "artist_urls"
    id = db.Column(db.Integer, primary_key=True)
    artist = db.relationship("Artist", back_populates="urls")
    artist_id = db.Column(db.Integer, db.ForeignKey("artists.id"))
    url = db.Column(db.String)
    type = db.Column(db.String)


class ArtistTag(db.Model):
    __tablename__ = "artist_tags"
    __versioned__ = {}
    id = db.Column(db.Integer, primary_key=True)
    tag_id = db.Column(db.String(50), db.ForeignKey("tags.tag"))
    artist_id = db.Column(db.Integer, db.ForeignKey("artists.id"))
    tag = db.relationship("Tag", back_populates="artists_with_tag")
    artist = db.relationship("Artist", back_populates="artist_tags")
    creator_id = db.Column(UUID, db.ForeignKey("users.id"))
    creator = db.relationship("User", back_populates="created_artist_tags")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class EventDateArtist(db.Model):
    __tablename__ = "event_date_artists"
    __versioned__ = {}

    id = db.Column(db.Integer, primary_key=True)

    artist = db.relationship("Artist", back_populates="events_with_artist")
    artist_id = db.Column(db.Integer, db.ForeignKey("artists.id"))

    event_date = db.relationship("EventDate", back_populates="artists")
    event_date_id = db.Column(db.Integer, db.ForeignKey("event_dates.id"))

    creator_id = db.Column(UUID, db.ForeignKey("users.id"))
    creator = db.relationship("User", back_populates="created_event_artists")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    start = db.Column(db.DateTime)
    start_naive = db.Column(db.DateTime)
    stage = db.Column(db.String)
