from datetime import datetime
from flask import current_app
from sqlalchemy import func, and_, Index, ForeignKeyConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.orderinglist import ordering_list
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy_continuum import transaction_class, version_class
from sqlalchemy import select
from sqlalchemy.orm import query_expression

from pmapi.extensions import db

# from pmapi.favorite_events.model import favorites_association_table
from pmapi.event_date.model import EventDate

# from pmapi.event_location.model import EventLocation


def create_tsvector(*args):
    # https://stackoverflow.com/questions/42388956/create-a-full-text-search-index-with-sqlalchemy-on-postgresql
    exp = args[0]
    for e in args[1:]:
        exp += " || " + e
    #    to_tsvector('english', title || ' ' || body))
    return func.to_tsvector("english", exp)

    # this table needs to be manually populated
    # two way relationship - so when I get an event it also has all event dates


user_event_following_table = db.Table(
    "user_event_following_table",
    db.Column("user_id", UUID, db.ForeignKey("users.id")),
    db.Column("event_id", db.Integer, db.ForeignKey("events.id")),
)

user_event_favorites_table = db.Table(
    "user_event_favorites_table",
    db.Column("user_id", UUID, db.ForeignKey("users.id")),
    db.Column("event_id", db.Integer, db.ForeignKey("events.id")),
)

event_page_views_table = db.Table(
    "event_page_views_table",
    db.Column("event_id", db.Integer, db.ForeignKey("events.id")),
    db.Column("user_id", UUID, db.ForeignKey("users.id")),
    db.Column("time", db.DateTime, default=datetime.utcnow),
)


class Event(db.Model):

    __versioned__ = {}
    __tablename__ = "events"
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

    followers = db.relationship(
        "User", back_populates="following_events", secondary=user_event_following_table
    )

    favorites = db.relationship(
        "User", back_populates="favorite_events", secondary=user_event_favorites_table
    )

    creator_id = db.Column(UUID, db.ForeignKey("users.id"))
    creator = db.relationship(
        "User",
        back_populates="created_events",
        foreign_keys=[creator_id],
    )

    host_id = db.Column(UUID, db.ForeignKey("users.id"))
    host = db.relationship(
        "User",
        back_populates="hosted_events",
        foreign_keys=[host_id],
    )

    is_favorited = query_expression()

    # deleted = db.Column(db.Boolean, nullable=False, default=False)

    name = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    description_attribute = db.Column(db.Text)

    rrule = db.relationship("Rrule", uselist=False, back_populates="event")

    event_dates = db.relationship("EventDate", back_populates="event")
    event_tags = db.relationship("EventTag", back_populates="event")
    event_contributions = db.relationship("EventContribution", back_populates="event")

    media_items = db.relationship(
        "MediaItem",
        back_populates="event",
        order_by="MediaItem.position",
        collection_class=ordering_list("position"),
    )

    settings = db.Column(JSONB)
    suggestions = db.relationship("SuggestedEdit", back_populates="event")
    reports = db.relationship("Report", back_populates="event")
    hidden = db.Column(db.Boolean, default=True)

    __ts_vector__ = create_tsvector(name, description)
    # this is an index for searching events
    # this was causing tests to fail, unsure if needed
    __table_args__ = (Index("idx_events_fts", __ts_vector__, postgresql_using="gin"),)

    @property
    def cover_items(self):
        # return first three items for cover images
        return self.media_items[0:3]

    def minified(self):
        return dict(
            name=self.name,
            id=self.id,
        )

    def next_event(self):
        now = datetime.utcnow()
        future_eventdates = [i for i in self.event_dates if i.start > now]
        if len(future_eventdates) > 0:
            return min(future_eventdates, key=lambda x: abs(x.start - now))
        else:
            return None

    def last_event_date(self):
        # returns the last event_date on the time line (could be in the past)
        eds = db.session.query(EventDate)
        eds = eds.filter(EventDate.event_id == self.id)
        eds = eds.order_by(EventDate.start.desc())
        return eds.first()

    def last_future_event_date(self):
        # returns the last event_date on the time line (only if it's in the future)
        now = datetime.utcnow()
        future_eventdates = [i for i in self.event_dates if i.start > now]
        if len(future_eventdates) > 0:
            return max(future_eventdates, key=lambda x: abs(x.start - now))
        else:
            return None

    def increment_page_views(self, user_id):
        db.engine.execute(
            event_page_views_table.insert(),
            user_id=user_id,
            event_id=self.id,
        )
        db.session.commit()

    @hybrid_property
    def page_views(self):
        return (
            db.session.query(event_page_views_table)
            .filter(event_page_views_table.c.event_id == self.id)
            .count()
        )

    @hybrid_property
    def last_transaction(self):
        Transaction = transaction_class(Event)
        EventVersion = version_class(Event)
        return (
            db.session.query(Transaction)
            .join(EventVersion, Transaction.id == EventVersion.transaction_id)
            .filter(EventVersion.id == self.id)
            .order_by(Transaction.id.desc())
            .first()
        )

    @last_transaction.expression
    def last_transaction(cls):
        # EventTransaction = transaction_class(Event)
        # return select(EventTransaction).order_by(EventTransaction.id.desc()).first()
        return None

    @property
    def future_event_dates(self):
        now = datetime.utcnow()
        eds = db.session.query(EventDate)
        eds = eds.filter(and_(EventDate.start >= now, EventDate.event_id == self.id))
        eds = eds.order_by(EventDate.start.asc())
        return eds.all()

    @property
    def future_event_dates_except_next(self):
        now = datetime.utcnow()
        eds = db.session.query(EventDate)
        eds = eds.filter(and_(EventDate.start >= now, EventDate.event_id == self.id))
        eds = eds.order_by(EventDate.start.asc())
        return eds.all()[1:]

        """
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
#        returns favorite status
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
    """

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
    __versioned__ = {}
    # max_num_of_occurances = db.Column(db.Integer, nullable=True)
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)
    event = db.relationship("Event", back_populates="rrule")
    # recurring_type  1=weekly, 2=monthly, 3=annually
    recurring_type = db.Column(db.Integer, nullable=False)
    # if separation_count is 0, no recurrance. 1, there is one interval,
    # if 2, two intervals (every two weeks) etc.
    separation_count = db.Column(db.Integer, nullable=True)
    day_of_week = db.Column(db.Integer, nullable=True)
    # 1st, 2nd, 3rd, 4th and 10 is last
    week_of_month = db.Column(db.Integer, nullable=True)
    # 1 - 31st
    day_of_month = db.Column(db.Integer, nullable=True)
    # 1 - 12
    month_of_year = db.Column(db.Integer, nullable=True)
    start_date_time = db.Column(db.String)  # naive datetime string
    end_date_time = db.Column(db.String)  # naive datetime string
    default_url = db.Column(db.String)
    default_ticket_url = db.Column(db.String)
    default_location_id = db.Column(db.Integer, db.ForeignKey("event_locations.id"))
    default_location = db.relationship("EventLocation")

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
