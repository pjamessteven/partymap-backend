from datetime import datetime
from sqlalchemy.orm import query_expression
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import func, extract, select
from sqlalchemy_continuum import version_class

from pmapi.extensions import db


class EventDate(db.Model):
    __versioned__ = {}
    __tablename__ = "event_dates"
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    event_id = db.Column(db.Integer, db.ForeignKey("events.id"))
    event = db.relationship("Event", back_populates="event_dates")
    tz = db.Column(db.String, nullable=False)

    start = db.Column(db.DateTime, nullable=False)
    end = db.Column(db.DateTime, nullable=False)
    start_naive = db.Column(db.DateTime, nullable=False)
    end_naive = db.Column(db.DateTime, nullable=False)
    # info can change for each event
    location_id = db.Column(db.Integer, db.ForeignKey("event_locations.id"))
    location = db.relationship("EventLocation", back_populates="event_dates")
    distance = query_expression()
    row_number = query_expression()
    artists = db.relationship("EventDateArtist", back_populates="event_date")
    description = db.Column(db.Text)
    description_attribute = db.Column(db.Text)
    url = db.Column(db.String)
    ticket_url = db.Column(db.String)
    cancelled = db.Column(db.Boolean, default=False)
    size = db.Column(db.Integer)

    contributions = db.relationship("EventContribution", back_populates="event_date")
    media_items = db.relationship("MediaItem", back_populates="event_date")
    suggestions = db.relationship("SuggestedEdit", back_populates="event_date")

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


"""
    @hybrid_property
    def previous_version(self):
        if self.transaction_id:
            for version in self.versions:
                if version.end_transaction_id == self.transaction_id:
                    return version
            return None
        return None

    @previous_version.expression
    def previous_version(cls):
        if cls.transaction_id:
            EventDateVersion = version_class(EventDate)
            return (
                select(EventDateVersion)
                .where(EventDateVersion.end_transaction_id == cls.transaction_id)
                .first()
            )
        else:
            return None
"""
