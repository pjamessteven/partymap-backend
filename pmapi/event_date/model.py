from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import query_expression
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import query_expression
from sqlalchemy import func, extract

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
    end = db.Column(db.DateTime, nullable=False)
    start_naive = db.Column(db.DateTime, nullable=False)
    end_naive = db.Column(db.DateTime, nullable=False)
    # info can change for each event
    location_id = db.Column(db.String, db.ForeignKey("event_locations.place_id"))
    location = db.relationship("EventLocation", back_populates="event_dates")
    distance = query_expression()
    # artists = db.relationship('EventArtist', back_populates="event_date")
    description = db.Column(db.Text)
    url = db.Column(db.String)
    ticket_url = db.Column(db.String)
    cancelled = db.Column(db.Boolean, default=False)
    size = db.Column(db.Integer)
    contributions = db.relationship("EventContribution", back_populates="event_date")
    media_items = db.relationship("MediaItem", back_populates="event_date")

    @hybrid_property
    def duration(self):
        return abs((self.end - self.start).days) + 1

    @duration.expression
    def duration(cls):
        return func.trunc(
            (extract("epoch", cls.end) - extract("epoch", cls.start))
            / 60
            / 60
            / 24  # seconds to minutes to hours to days
            + 1
        )
