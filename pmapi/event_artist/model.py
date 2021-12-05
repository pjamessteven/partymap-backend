from datetime import datetime

from sqlalchemy.dialects.postgresql import UUID

from pmapi.extensions import db


class Artist(db.Model):
    __tablename__ = "artists"
    id = db.Column(db.Integer, primary_key=True)
    mbid = db.Column(db.String(100))
    name = db.Column(db.String(50), nullable=False)
    events_with_artist = db.relationship("EventDateArtist", back_populates="artist")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # artist specific stuff
    description = db.Column(db.Text)
    disambiguation = db.Column(db.Text)
    area = db.Column(db.Text)
    urls = db.relationship("ArtistUrl")


class ArtistUrl(db.Model):
    __tablename__ = "artist_urls"
    id = db.Column(db.Integer, primary_key=True)
    artist = db.relationship("Artist", back_populates="urls")
    artist_id = db.Column(db.Integer, db.ForeignKey("artists.id"))
    url = db.Column(db.String)
    type = db.Column(db.String)


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
