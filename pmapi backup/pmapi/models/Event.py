from pmapi.application import db
import calendar
from datetime import datetime
from flask import Flask
from sqlalchemy_continuum import transaction_class

favorites_association_table = db.Table('favorites_association',
    db.Column('user', db.Integer, db.ForeignKey('users.id')),
    db.Column('event', db.Integer, db.ForeignKey('events.id'))
    )

class Event(db.Model):
    #__versioned__ = {}
    __tablename__ = 'events'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    url = db.Column(db.String, nullable=False)
    lat = db.Column(db.Float, nullable=False)
    lng = db.Column(db.Float, nullable=False)
    city = db.Column(db.String)
    country = db.Column(db.String)
    country_code = db.Column(db.String)
    event_start = db.Column(db.Integer, nullable=True)
    event_end = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.Integer, default=datetime.utcnow())
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    description = db.Column(db.Text)
    event_tags = db.relationship('EventTag', back_populates="event")
    event_artists = db.relationship('EventArtist', back_populates="event")
    event_images = db.relationship('EventImage', backref="event", lazy=False)
    contributions = db.relationship('EventContribution', backref="event", lazy=False)

    #basic info which will be used for map points to speed up initial load time
    def minified(self):
        return dict(
            id=self.id,
            lat=self.lat,
            lng=self.lng,
        )

    def to_dict(self, current_user=None):
        #get revisions then invert list
        #revisions = [{
        #    'changes': version.changeset,
        #    'user': version.transaction.user.username,
        #    'date': version.transaction.issued_at
        #    } for version in self.versions]
        #revisions = revisions[::-1]
        self.contributions.sort(key=lambda x: x.votes, reverse=True)
        self.event_images.sort(key=lambda x: x.votes, reverse=True)
        self.event_tags.sort(key=lambda x: len(x.tag.events_with_tag), reverse=True)
        self.event_artists.sort(key=lambda x: x.votes, reverse=True)
        #THIS USER_ID SHIT IS DEFUNCT BECAUSE OF FLASK-LOGIN SESSIONS
        #if user is logged in, include upvote status etc.
        if current_user:
            return dict(id=self.id,
                        name=self.name,
                        description=self.description,
                        lat=self.lat,
                        lng=self.lng,
                        country=self.country,
                        country_code=self.country_code,
                        city=self.city,
                        event_start=self.event_start,
                        event_end= self.event_end,
                        created_at=self.created_at,
                        creator_id=self.creator_id,
                        event_images=[image.to_dict() for image in self.event_images],
                        contributions=[contribution.to_dict() for contribution in self.contributions],
                        url=self.url,
                        event_tags=[tag.to_dict() for tag in self.event_tags],
                        event_artists=[artist.to_dict() for artist in self.event_artists],
                        favorited=self.is_favorited(current_user.id),
                #        revisions=self.versions.count(),
                #        revision_history=revisions
                        )

        else:
            images_sorted = self.event_images.sort(key=lambda x: x.votes, reverse=True)
            return dict(id=self.id,
                        name=self.name,
                        description=self.description,
                        lat=self.lat,
                        lng=self.lng,
                        country=self.country,
                        country_code=self.country_code,
                        city=self.city,
                        event_start=self.event_start,
                        event_end= self.event_end,
                        created_at=self.created_at,
                        creator_id=self.creator_id,
                        event_images=[image.to_dict() for image in self.event_images],
                        contributions=[contribution.to_dict() for contribution in self.contributions],
                        url=self.url,
                        event_tags=[tag.to_dict() for tag in self.event_tags],
                        event_artists=[artist.to_dict() for artist in self.event_artists],
                #        revisions=self.versions.count(),
                #        revision_history=revisions
                        )

    def favorite(self, user_id):
        _faved = self.is_favorited(user_id)
        if _faved is False:
            db.engine.execute(
                favorites_association_table.insert(),
                user   = user_id,
                event = self.id
                )
            db.session.commit()
            return True
        if _faved is True:
            db.engine.execute(
                favorites_association_table.delete(
                    db.and_(
                        favorites_association_table.c.user == user_id,
                        favorites_association_table.c.event == self.id
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
                favorites_association_table.c.user == user_id
            ))
        rs = db.engine.execute(select).fetchall()
        if len(rs) > 0:
            return True
        else:
            return False
