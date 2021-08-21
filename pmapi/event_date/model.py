from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import query_expression
import uuid

from pmapi.extensions import db


class EventDate(db.Model):
    __versioned__ = {}
    __tablename__ = "event_dates"
    id = db.Column(UUID, primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    event_id = db.Column(UUID, db.ForeignKey("events.id"))
    event = db.relationship("Event", back_populates="event_dates")
    tz = db.Column(db.String, nullable=False)

    start = db.Column(db.DateTime, nullable=False)
    end = db.Column(db.DateTime, nullable=True)
    start_naive = db.Column(db.DateTime, nullable=False)
    end_naive = db.Column(db.DateTime, nullable=True)
    start_time = db.Column(db.Boolean)
    end_time = db.Column(db.Boolean)
    # info can change for each event
    location_id = db.Column(db.String, db.ForeignKey("event_locations.place_id"))
    location = db.relationship("EventLocation", back_populates="event_dates")
    distance = query_expression()
    # artists = db.relationship('EventArtist', back_populates="event_date")
    description = db.Column(db.Text)
    url = db.Column(db.String)
    cancelled = db.Column(db.Boolean, default=False)

    contributions = db.relationship("EventContribution", back_populates="event_date")
    media_items = db.relationship("MediaItem", back_populates="event_date")
