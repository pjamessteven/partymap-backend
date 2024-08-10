from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from flask_login import (
    login_user,
)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import select, join
from sqlalchemy.orm import query_expression
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy_continuum import transaction_class, version_class

from pmapi.extensions import db

# from pmapi.favorite_events.model import favorites_association_table
from pmapi.utils import ROLES
import pmapi.exceptions as exc
import pmapi.validate as validate
from pmapi.media_item.model import MediaItem

from pmapi.event.model import (
    Event,
    user_event_following_table,
)

from pmapi.event_date.model import (
    user_event_date_interested_table,
    user_event_date_going_table
)


import uuid

app = Flask(__name__)


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(UUID, primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    role = db.Column(db.Integer, nullable=False,
                     default=ROLES["UNPRIVILIGED_USER"])
    last_active = db.Column(db.DateTime, default=datetime.utcnow)
    # Username can be null before social user has chosen a username
    username = db.Column(db.String(80), unique=True, nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password = db.Column(db.String(255), nullable=True)
    alias = db.Column(db.String(200))
    description = db.Column(db.String(1000))
    oauth = db.Column(db.Boolean, unique=False, default=False)
    one_off_auth_token = db.Column(UUID)

    status = db.Column(
        ENUM("active", "disabled", "pending", name="user_status"), default="pending"
    )
    karma = db.Column(db.Integer, default=0)
    notifications = db.relationship(
        "UserNotification", back_populates="user", cascade="all, delete-orphan"
    )
    avatar_id = db.Column(db.Integer, db.ForeignKey(MediaItem.id))
    avatar = db.relationship("MediaItem", uselist=False,
                             foreign_keys=[avatar_id], back_populates="is_user_avatar", primaryjoin="User.avatar_id == MediaItem.id")

    following_events = db.relationship(
        "Event", back_populates="followers", secondary=user_event_following_table
    )

    going_event_dates = db.relationship(
        "EventDate", back_populates="going", secondary=user_event_date_going_table
    )

    interested_event_dates = db.relationship(
        "EventDate", back_populates="interested", secondary=user_event_date_interested_table
    )

    created_events = db.relationship(
        "Event",
        back_populates="creator",
        primaryjoin="Event.creator_id == User.id",
    )

    hosted_events = db.relationship(
        "Event",
        back_populates="host",
        primaryjoin="Event.host_id == User.id",
    )

    created_suggestions = db.relationship(
        "SuggestedEdit",
        back_populates="creator",
        primaryjoin="SuggestedEdit.creator_id == User.id",
    )

    created_reviews = db.relationship(
        "EventReview",
    back_populates="creator",
        primaryjoin="EventReview.creator_id == User.id",
    )
    #    created_event_artists = db.relationship(
    #        'EventArtist', back_populates="creator")
    created_media_items = db.relationship(
        "MediaItem", back_populates="creator", primaryjoin="MediaItem.creator_id == User.id")
    created_event_locations = db.relationship(
        "EventLocation", back_populates="creator")
    created_event_tags = db.relationship("EventTag", back_populates="creator")
    created_artist_tags = db.relationship(
        "ArtistTag", back_populates="creator")
    created_event_artists = db.relationship(
        "EventDateArtist", back_populates="creator")
    created_reports = db.relationship("Report", back_populates="creator")
    created_feedback = db.relationship("Feedback", back_populates="creator")

    def set_password(self, password):
        validate.password(password)
        self.password = generate_password_hash(password, method="sha256")

    @property
    def active(self):
        return self.status == "active"

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return self.status == "active"

    @property
    def is_anonymous(self):
        return False

    @hybrid_property
    def oauth_obj(self):
        return OAuth.query.filter(OAuth.user_id == self.id).first()

    @oauth_obj.expression
    def oauth_obj(self):
        return select(OAuth).where(OAuth.user_id == self.id)

    @hybrid_property
    def version_count(self):
        EventTransaction = transaction_class(Event)
        EventVersion = version_class(Event)
        query = (
            db.session.query(EventTransaction)
            .join(EventVersion, EventTransaction.id == EventVersion.transaction_id)
            .filter(EventTransaction.user_id == self.id)
        )
        return query.count()

    @version_count.expression
    def version_count(self):
        EventTransaction = transaction_class(Event)
        EventVersion = version_class(Event)
        return (
            select(
                join(
                    EventTransaction,
                    EventVersion,
                    EventTransaction.id == EventVersion.transaction_id,
                )
            )
            .where(EventTransaction.user_id == self.id)
            .count()
        )

    def deactivate(self):
        self.status = "disabled"

    def activate(self):
        """activate a "pending" account"""
        self.status = "active"
        return self

    def get_id(self):
        return str(self.id).encode("utf-8").decode("utf-8")


"""
    def get_favorites(self):
        select = favorites_association_table.select(
            favorites_association_table.c.user == self.id
        )
        rs = db.engine.execute(select).fetchall()
        events = []
        events.sort(key=lambda x: x.start, reverse=True)
        for r in rs:
            events.append(Event.query.get(r[1]))
        return events


    def get_karma(self):
        fetch the number of votes this user has had on his/her reviews and images

        add tags later????
        review_ids = [c.id for c in self.reviews]
        ecupvotes = eventreview_upvotes.select(db.and_(
            eventreview_upvotes.c.eventreview_id.in_(review_ids),
            eventreview_upvotes.c.user_id != self.id
        )
        )
        ecdownvotes = eventreview_downvotes.select(db.and_(
            eventreview_downvotes.c.eventreview_id.in_(review_ids),
            eventreview_downvotes.c.user_id != self.id
        )
        )
        ecupvotesresults = db.engine.execute(ecupvotes)
        ecdownvotesresults = db.engine.execute(ecdownvotes)

        eventimage_ids = [c.id for c in self.event_images]
        eiupvotes = eventimage_upvotes.select(db.and_(
            eventimage_upvotes.c.eventimage_id.in_(eventimage_ids),
            eventimage_upvotes.c.user_id != self.id
        )
        )
        eidownvotes = eventimage_downvotes.select(db.and_(
            eventimage_downvotes.c.eventimage_id.in_(eventimage_ids),
            eventimage_downvotes.c.user_id != self.id
        )
        )
        eiupvotesresults = db.engine.execute(eiupvotes)
        eidownvotesresults = db.engine.execute(eidownvotes)

        total = ecupvotes.rowcount-
        ecdownvotes.rowcount+eiupvotes.rowcount-eidownvotes.rowcount
        return total

"""


class OAuth(OAuthConsumerMixin, db.Model):
    provider_user_id = db.Column(db.String(256), unique=True, nullable=False)
    user_id = db.Column(UUID, db.ForeignKey(User.id))
    user = db.relationship(User)
