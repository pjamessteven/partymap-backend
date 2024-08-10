from datetime import datetime
from sqlalchemy.orm import query_expression
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import func, extract, select
from sqlalchemy_continuum import version_class
from sqlalchemy.dialects.postgresql import UUID

from pmapi.extensions import db


user_event_date_going_table = db.Table(
    "user_event_date_going_table",
    db.Column("user_id", UUID, db.ForeignKey("users.id")),
    db.Column("event_date_id", db.Integer, db.ForeignKey("event_dates.id")),
)

user_event_date_interested_table = db.Table(
    "user_event_date_interested_table",
    db.Column("user_id", UUID, db.ForeignKey("users.id")),
    db.Column("event_date_id", db.Integer, db.ForeignKey("event_dates.id")),
)


class EventDateTicket(db.Model):
    __versioned__ = {'versioning_relations': ['event_date']}
    __tablename__ = "event_date_tickets"
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"))
    event = db.relationship("Event", back_populates="event_tickets")
    event_date = db.relationship("EventDate", back_populates="tickets")
    event_date_id = db.Column(db.Integer, db.ForeignKey("event_dates.id"))
    url = db.Column(db.String)
    description = db.Column(db.String)
    price_min = db.Column(db.Integer)
    price_max = db.Column(db.Integer)
    price_currency_code = db.Column(db.String)


class EventDate(db.Model):
    __versioned__ = {'versioning_relations': ['artists', 'location', 'tickets', 'media_items', 'reviews']}
    __tablename__ = "event_dates"
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    interested = db.relationship(
        "User", back_populates="interested_event_dates", secondary=user_event_date_interested_table
    )
    going = db.relationship(
        "User", back_populates="going_event_dates", secondary=user_event_date_going_table
    )

    event_id = db.Column(db.Integer, db.ForeignKey("events.id"))
    event = db.relationship("Event", back_populates="event_dates")
    tz = db.Column(db.String, nullable=False)

    start = db.Column(db.DateTime, nullable=False)
    end = db.Column(db.DateTime, nullable=False)
    start_naive = db.Column(db.DateTime, nullable=False)
    end_naive = db.Column(db.DateTime, nullable=False)
    date_confirmed = db.Column(db.Boolean, default=True)
    # info can change for each event
    location_id = db.Column(db.Integer, db.ForeignKey("event_locations.id"))
    location = db.relationship("EventLocation", back_populates="event_dates")
    distance = query_expression()
    row_number = query_expression()
    artists = db.relationship("EventDateArtist", back_populates="event_date")
    description = db.Column(db.Text)
    description_attribute = db.Column(db.Text)
    url = db.Column(db.String)
    tickets = db.relationship("EventDateTicket", back_populates="event_date")
    cancelled = db.Column(db.Boolean, default=False)
    size = db.Column(db.Integer)

    reviews = db.relationship(
        "EventReview", back_populates="event_date")
    media_items = db.relationship("MediaItem", back_populates="event_date")
    suggestions = db.relationship("SuggestedEdit", back_populates="event_date")

    user_going = query_expression()
    user_interested = query_expression()

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
