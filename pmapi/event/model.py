from datetime import datetime
from flask import current_app
from sqlalchemy import Index, func
from sqlalchemy import and_
from sqlalchemy.dialects.postgresql import JSONB, UUID
import uuid

import pmapi.activity.controllers as activities
from pmapi.extensions import db
from pmapi.favorite_events.model import favorites_association_table
from pmapi.event_date.model import EventDate


def create_tsvector(*args):
    # https://stackoverflow.com/questions/42388956/create-a-full-text-search-index-with-sqlalchemy-on-postgresql
    exp = args[0]
    for e in args[1:]:
        exp += " || " + e
    #    to_tsvector('english', title || ' ' || body))
    return func.to_tsvector("english", exp)


# this table needs to be manually populated
# two way relationship - so when I get an event it also has all event dates


class Event(db.Model):
    __versioned__ = {}
    __tablename__ = "events"

    id = db.Column(UUID, primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator_id = db.Column(UUID, db.ForeignKey("users.id"))
    creator = db.relationship(
        "User", back_populates="created_events", foreign_keys=[creator_id]
    )

    name = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    rrule = db.relationship("Rrule", uselist=False, back_populates="event")

    event_dates = db.relationship("EventDate", back_populates="event")
    event_tags = db.relationship("EventTag", back_populates="event")
    # event_contributions = db.relationship(
    #    'EventContribution', back_populates="event")
    event_images = db.relationship("EventImage", back_populates="event")

    default_url = db.Column(db.String)
    default_location = db.relationship("EventLocation", back_populates="event")
    default_location_place_id = db.Column(
        db.String, db.ForeignKey("event_locations.place_id")
    )

    settings = db.Column(JSONB)

    __ts_vector__ = create_tsvector(name, description)
    # this is an index for searching events
    # this was causing tests to fail, unsure if needed
    # __table_args__ = (Index("idx_events_fts", __ts_vector__, postgresql_using="gin"),)

    def minified(self):
        return dict(
            name=self.name,
            id=self.id,
        )

    def to_dict(self, current_user=None, activity=True):
        # images_sorted =
        # self.event_contributions.sort(key=lambda x: x.votes,
        # reverse=True)
        # if user is logged in, include upvote status etc.
        if current_user:
            if self.rrule:
                recurring = self.rrule.to_dict()
            else:
                recurring = None
            return dict(
                id=self.id,
                name=self.name,
                created_at=self.created_at,
                creator_id=self.creator_id,
                event_images=[i.to_dict() for i in self.event_images],
                description=self.description,
                url=self.default_url,
                favorited=self.is_favorited(current_user.id),
                event_dates=[ed.to_dict() for ed in self.future_event_dates()],
                # revisions=self.versions.count(),
                # most_recent_activity=activities.get_most_recent_activity_for_item(self)
                # if activity
                # else None,
                event_tags=[tag.to_dict() for tag in self.event_tags],
                rrule=recurring,
                # settings=self.settings,
            )

        else:
            if self.rrule:
                recurring = self.rrule.to_dict()
            else:
                recurring = None
            return dict(
                id=self.id,
                name=self.name,
                created_at=self.created_at,
                creator_id=self.creator_id,
                # owners=[o.username for o in self.owners],
                event_images=[i.to_dict() for i in self.event_images],
                description=self.description,
                url=self.default_url,
                event_tags=[tag.to_dict() for tag in self.event_tags],
                event_dates=[ed.to_dict() for ed in self.future_event_dates()],
                # revisions=self.versions.count(),
                # most_recent_activity=activities.get_most_recent_activity_for_item(self)
                # if activity
                # else None,
                rrule=recurring,
                # settings=self.settings,
            )

    def next_event(self):
        now = datetime.utcnow()
        future_eventdates = [i for i in self.event_dates if i.event_start > now]
        if len(future_eventdates) > 0:
            return min(future_eventdates, key=lambda x: abs(x.event_start - now))
        else:
            return None

    def last_event(self):
        now = datetime.utcnow()
        future_eventdates = [i for i in self.event_dates if i.event_start > now]
        if len(future_eventdates) > 0:
            return max(future_eventdates, key=lambda x: abs(x.event_start - now))
        else:
            return None

    def future_event_dates(self):
        now = datetime.utcnow()
        eds = (
            db.session.query(EventDate)
            .filter(and_(EventDate.event_start >= now, EventDate.event_id == self.id))
            .order_by(EventDate.event_start.asc())
            .all()
        )
        return eds

    def favorite(self, user_id):
        _faved = self.is_favorited(user_id)
        if _faved is False:
            db.engine.execute(
                favorites_association_table.insert(), user=user_id, event=self.id
            )
            db.session.commit()
            return True
        if _faved is True:
            db.engine.execute(
                favorites_association_table.delete(
                    db.and_(
                        favorites_association_table.c.user == user_id,
                        favorites_association_table.c.event == self.id,
                    )
                )
            )
            db.session.commit()
            return False

    def is_favorited(self, user_id):
        """
        returns favorite status
        """
        select = favorites_association_table.select(
            db.and_(
                favorites_association_table.c.event == self.id,
                favorites_association_table.c.user == user_id,
            )
        )
        rs = db.engine.execute(select).fetchall()
        if len(rs) > 0:
            return True
        else:
            return False

    def eventDates(self):
        return [ed.minified() for ed in self.event_dates]

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
        print(revisions)
        revisions = revisions[::-1]
        print(revisions)
        return revisions

    def getUrl(self):
        return current_app.config["WEBSITE_URL"] + "/event/" + self.id


class Rrule(db.Model):
    __tablename__ = "rrules"
    # max_num_of_occurances = db.Column(db.Integer, nullable=True)
    event_id = db.Column(
        UUID, db.ForeignKey("events.id"), primary_key=True, nullable=False
    )
    event = db.relationship("Event", back_populates="rrule")
    # recurring_type 0=daily(not a thing), 1=weekly, 2=monthly, 3=annually
    recurring_type = db.Column(db.Integer, nullable=False)
    # if separation_count is 1, there is one interval skipped,
    # if 2, two intervals skipped etc.
    separation_count = db.Column(db.Integer, nullable=True)
    day_of_week = db.Column(db.Integer, nullable=True)
    # 1st, 2nd, 3rd, 4th and 10 is last
    week_of_month = db.Column(db.Integer, nullable=True)
    # 1 - 31st
    day_of_month = db.Column(db.Integer, nullable=True)
    # 1 - 12
    month_of_year = db.Column(db.Integer, nullable=True)

    def to_dict(self):
        return dict(
            event_id=self.event_id,
            recurring_type=self.recurring_type,
            separation_count=self.separation_count,
            # max_num_of_occurances=self.max_num_of_occurances,
            day_of_week=self.day_of_week,
            week_of_month=self.week_of_month,
            day_of_month=self.day_of_month,
            month_of_year=self.month_of_year,
        )
