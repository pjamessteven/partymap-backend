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

    creator_id = db.Column(UUID, db.ForeignKey("users.id"))
    creator = db.relationship("User", back_populates="created_event_dates")

    event_id = db.Column(UUID, db.ForeignKey("events.id"))
    event = db.relationship("Event", back_populates="event_dates")
    tz = db.Column(db.String, nullable=False)

    start = db.Column(db.DateTime, nullable=False)
    end = db.Column(db.DateTime, nullable=True)
    start_naive = db.Column(db.DateTime, nullable=False)
    end_naive = db.Column(db.DateTime, nullable=True)
    # info can change for each event
    location_id = db.Column(db.String, db.ForeignKey("event_locations.place_id"))
    location = db.relationship("EventLocation", back_populates="event_dates")
    distance = query_expression()
    # artists = db.relationship('EventArtist', back_populates="event_date")
    description = db.Column(db.Text)
    url = db.Column(db.String)
    cancelled = db.Column(db.Boolean, default=False)

    contributions = db.relationship("EventContribution", back_populates="event_date")
    event_album_id = db.Column(UUID, db.ForeignKey("event_albums.id"))
    event_album = db.relationship("EventAlbum", uselist=False)

    def minified(self):

        return dict(
            id=self.id,
            event_id=self.event_id,
            name=self.event.name,
            start=self.start,
            end=self.end,
            start_naive=self.start_naive,
            end_naive=self.end_naive,
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
                start=self.start,
                end=self.end,
                start_naive=self.start_naive,
                end_naive=self.end_naive,
                tz=self.tz,
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
                start=self.start,
                end=self.end,
                start_naive=self.start_naive,
                end_naive=self.end_naive,
                tz=self.tz,
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
