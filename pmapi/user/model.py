from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from flask_login import (
    login_user,
)
from pmapi.extensions import db

# from pmapi.favorite_events.model import favorites_association_table
from pmapi.utils import ROLES
import pmapi.exceptions as exc

from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.dialects.postgresql import UUID
import uuid

app = Flask(__name__)


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(UUID, primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    role = db.Column(db.Integer, nullable=False, default=ROLES["UNPRIVILIGED_USER"])
    last_active = db.Column(db.DateTime, default=datetime.utcnow)
    # Username can be null before social user has chosen a username
    username = db.Column(db.String(80), unique=True, nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=True)
    oauth = db.Column(db.Boolean, unique=False, default=False)
    status = db.Column(
        ENUM("active", "disabled", "pending", name="user_status"), default="pending"
    )
    karma = db.Column(db.Integer, default=0)
    notifications = db.relationship(
        "UserNotification", back_populates="user", cascade="all, delete-orphan"
    )

    created_events = db.relationship("Event", back_populates="creator")
    created_event_dates = db.relationship("EventDate", back_populates="creator")
    #    created_contributions = db.relationship(
    #        'EventContribution', back_populates="creator")
    #    created_event_artists = db.relationship(
    #        'EventArtist', back_populates="creator")
    created_event_images = db.relationship("EventImage", back_populates="creator")
    created_event_locations = db.relationship("EventLocation", back_populates="creator")
    created_event_tags = db.relationship("EventTag", back_populates="creator")

    # override init method to hash password when new user created

    def __init__(self, email, username=None, password=None, role=None, status=None):
        self.email = email
        if username is not None:
            self.username = username
        if password is not None:
            self.password = generate_password_hash(password, method="sha256")
        if role is not None:
            self.role = role
        if status is not None:
            self.status = status

    @classmethod
    def authenticate(cls, **kwargs):
        email = kwargs.get("email")
        password = kwargs.get("password")
        remember = kwargs.get("remember", False)

        if not email or not password:
            raise exc.LoginRequired()

        user = cls.query.filter_by(email=email).first()

        # don't allow pending or disabled accounts to login
        if user.status == "disabled":
            raise exc.UserDisabled()
        elif user.status == "pending":
            raise exc.UserPending()

        if not user or not check_password_hash(user.password, password):
            raise exc.LoginRequired()

        # flask-login
        login_user(user, remember=remember)

        return user

    def to_dict(self):
        return dict(
            id=self.id, username=self.username, email=self.email, status=self.status
        )

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
        fetch the number of votes this user has had on his/her contributions and images

        add tags later????
        contribution_ids = [c.id for c in self.contributions]
        ecupvotes = eventcontribution_upvotes.select(db.and_(
            eventcontribution_upvotes.c.eventcontribution_id.in_(contribution_ids),
            eventcontribution_upvotes.c.user_id != self.id
        )
        )
        ecdownvotes = eventcontribution_downvotes.select(db.and_(
            eventcontribution_downvotes.c.eventcontribution_id.in_(contribution_ids),
            eventcontribution_downvotes.c.user_id != self.id
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
