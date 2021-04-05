import calendar
from datetime import datetime
from flask import Flask
from sqlalchemy_continuum import transaction_class
from sqlalchemy.dialects.postgresql import UUID
import uuid

from pmapi.extensions import db

import pmapi.activity.controllers as activities


class EventDate(db.Model):
    __versioned__ = {}
    __tablename__ = "event_dates"
    id = db.Column(UUID, primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator_id = db.Column(UUID, db.ForeignKey("users.id"))
    creator = db.relationship("User", back_populates="created_event_dates")

    event_id = db.Column(UUID, db.ForeignKey("events.id"))
    event = db.relationship("Event", back_populates="event_dates")
    tz = db.Column(db.String, nullable=False)
    event_start = db.Column(db.DateTime, nullable=False)
    event_start_naive = db.Column(db.DateTime, nullable=False)
    event_end = db.Column(db.DateTime, nullable=True)
    event_end_naive = db.Column(db.DateTime, nullable=True)
    all_day = db.Column(db.Boolean, default=True, nullable=False)
    # info can change for each event
    location_id = db.Column(db.String, db.ForeignKey("event_locations.place_id"))
    location = db.relationship("EventLocation", back_populates="event_dates")
    # artists = db.relationship('EventArtist', back_populates="event_date")
    # contributions = db.relationship('EventContribution', back_populates="event_date")
    description = db.Column(db.Text)
    url = db.Column(db.String)
    cancelled = db.Column(db.Boolean, default=False)

    def minified(self):

        return dict(
            id=self.id,
            event_id=self.event_id,
            name=self.event.name,
            start=self.event_start,
            end=self.event_end,
            start_naive=self.event_start_naive,
            end_naive=self.event_end_naive,
            tz=self.tz,
            tags=[et.minified() for et in self.event.event_tags],
            city=self.location.city,
            cancelled=self.cancelled,
        )

    def to_dict(self, current_user=None, activity=True):
        if current_user:
            return dict(
                id=self.id,
                event_id=self.event_id,
                event_start=self.event_start,
                event_end=self.event_end,
                start_naive=self.event_start_naive,
                end_naive=self.event_end_naive,
                tz=self.tz,
                all_day=self.all_day,
                description=self.description,
                url=self.url,
                created_at=self.created_at,
                # most_recent_activity=activities.get_most_recent_activity_for_item(self)
                # if activity
                # else None,
                location=self.location.to_dict(),
                cancelled=self.cancelled,
            )
        else:
            return dict(
                id=self.id,
                event_id=self.event_id,
                event_start=self.event_start,
                event_end=self.event_end,
                start_naive=self.event_start_naive,
                end_naive=self.event_end_naive,
                tz=self.tz,
                all_day=self.all_day,
                description=self.description,
                url=self.url,
                created_at=self.created_at,
                # most_recent_activity=activities.get_most_recent_activity_for_item(self)
                # if activity
                # else None,
                location=self.location.to_dict(),
                cancelled=self.cancelled,
            )

    def revisions(self):
        # get revisions then invert list
        revisions = [
            {
                "changes": version.changeset,
                "user": version.transaction.user.username,
                "date": version.transaction.issued_at,
            }
            for version in self.versions
        ]
        revisions = revisions[::-1]
        return revisions
