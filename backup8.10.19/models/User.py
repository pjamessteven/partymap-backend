"""
models.py
- Data classes for the surveyapi application
"""

from datetime import datetime
import calendar
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask
from flask_login import LoginManager, UserMixin, login_user, logout_user
from pmapi.models.Event import *

import os
from pmapi.application import db, lm



app = Flask(__name__)




class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow())
    username = db.Column(db.String(80), unique=True, nullable=False)
    social_id = db.Column(db.String(64), unique=True, nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    oath = db.Column(db.Boolean, unique=False, default=False)
    karma = db.Column(db.Integer, default=0)

    events = db.relationship('Event', backref="creator", lazy=False)
    #it would be cool to show all contributions by a user
    #contributions = db.relationship('EventContribution', backref="contributor", lazy=False)
    event_images = db.relationship('EventImage', backref="imageUploader", lazy=False)
    event_tags = db.relationship('EventTag', backref="tagger", lazy=False)

    #override init method to hash password when new user created
    def __init__(self, email, password, username):
        self.email = email
        self.username = username
        self.password = generate_password_hash(password, method='sha256')

    @classmethod
    def authenticate(cls, **kwargs):
        email = kwargs.get('email')
        password = kwargs.get('password')

        if not email or not password:
            return None

        user = cls.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password, password):
            return None

        return user

    def to_dict(self):
        return dict(id=self.id,
                    username=self.username,
                    email=self.email,
                    favorite_events=[event.to_dict() for event in self.get_favorites()])
    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_favorites(self):
        select = favorites_association_table.select(
                favorites_association_table.c.user == self.id
            )
        rs = db.engine.execute(select).fetchall()
        events = []
        events.sort(key=lambda x: x.event_start, reverse=True)
        for r in rs:
            events.append(Event.query.get(r[1]))
        return events

    def get_id(self):
        return str(self.id).encode("utf-8").decode("utf-8")

    def get_karma(self):
        """
        fetch the number of votes this user has had on his/her contributions and images

        add tags later????
        """
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

        total = ecupvotes.rowcount-ecdownvotes.rowcount+eiupvotes.rowcount-eidownvotes.rowcount
        return total
