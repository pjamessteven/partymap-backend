from pmapi.application import db
import calendar
from datetime import datetime
from flask import Flask
from sqlalchemy_continuum import transaction_class

favorites_association_table = db.Table('favorites_association',
    db.Column('user', db.Integer, db.ForeignKey('users.id')),
    db.Column('event', db.Integer, db.ForeignKey('events.id'))
    )

'''
class EventInstanceException(db.Model):
    __tablename__ = 'event_instance_exceptions'

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    is_cancelled = db.Column(db.Boolean, default=False)
    is_rescheduled = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return dict(
            id = self.id,
            event_id = self.event_id,
            is_cancelled = self.is_cancelled,
            is_rescheduled = self.is_rescheduled
        )
'''


class Rrule(db.Model):
    __tablename__ = 'recurring_patterns'
    #max_num_of_occurances = db.Column(db.Integer, nullable=True)

    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), primary_key=True, nullable=False)
    # recurring_type 0=daily(not a thing), 1=weekly, 2=monthly, 3=annually
    recurring_type = db.Column(db.Integer, nullable=False)
    #if separation_count is 1, there is one interval skipped, if 2, two intervals skipped etc.
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
            max_num_of_occurances=self.max_num_of_occurances,
            day_of_week=self.day_of_week,
            week_of_month=self.week_of_month,
            day_of_month=self.day_of_month,
            month_of_year=self.month_of_year
        )

#this table needs to be manually populated
#two way relationship - so when I get an event it also has all event dates
class EventDate(db.Model):
    __versioned__ = {}
    __tablename__ = 'event_dates'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'))
    event = db.relationship('Event', back_populates="event_dates")

    event_start = db.Column(db.DateTime, nullable=False)
    event_end = db.Column(db.DateTime, nullable=True)
    all_day = db.Column(db.Boolean, default=True, nullable=False)

    #info can change for each event
    event_artists = db.relationship('EventArtist', back_populates="event_date")
    event_images = db.relationship('EventImage', backref="event_date", lazy=False)
    description = db.Column(db.Text)
    url = db.Column(db.String, nullable=False)
    lat = db.Column(db.Float, nullable=False)
    lng = db.Column(db.Float, nullable=False)
    city = db.Column(db.String)
    country = db.Column(db.String)
    country_code = db.Column(db.String)
    event_tags = db.relationship('EventTag', back_populates="event_date")

    created_at = db.Column(db.DateTime, default=datetime.utcnow())

    def minified(self):
        return dict(id=self.id,
                    event_id=self.event_id,
                    lat=self.lat,
                    lng=self.lng,
                    name=self.event.name)

    def to_dict(self, current_user=None):
        revisions = [{
            'changes': version.changeset,
            'user': version.transaction.user.username,
            'date': version.transaction.issued_at
            } for version in self.versions]
        revisions = revisions[::-1]
        event_start = self.event_start.timestamp()*1000
        event_end = None
        if self.event_end is not None:
            event_end = self.event_end.timestamp()*1000
        if current_user:
            return dict(id=self.id,
                        event_id=self.event_id,
                        event=self.event.to_dict(current_user),
                        event_start=event_start,
                        event_end=event_end,
                        all_day=self.all_day,
                        description=self.description,
                        url=self.url,
                        lat=self.lat,
                        lng=self.lng,
                        country=self.country,
                        country_code=self.country_code,
                        city=self.city,
                        event_artists=[artist.to_dict() for artist in self.event_artists],
                        event_images=[image.to_dict() for image in self.event_images],
                        created_at=self.created_at,
                        revisions=self.versions.count(),
                        revision_history=revisions)
        else:
            return dict(id=self.id,
                        event_id=self.event_id,
                        event=self.event.to_dict(),
                        event_start=event_start,
                        event_end=event_end,
                        all_day=self.all_day,
                        description=self.description,
                        url=self.url,
                        lat=self.lat,
                        lng=self.lng,
                        country=self.country,
                        country_code=self.country_code,
                        city=self.city,
                        event_artists=[artist.to_dict() for artist in self.event_artists],
                        event_images=[image.to_dict() for image in self.event_images],
                        created_at=self.created_at,
                        revisions=self.versions.count(),
                        revision_history=revisions)


class Event(db.Model):
    __versioned__ = {}
    __tablename__ = 'events'

    recurring = db.Column(db.Integer, nullable=False, default=False)
    event_dates = db.relationship("EventDate", back_populates="event")
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow())
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    #basic info which will be used for map points to speed up initial load time
    def minified(self):
        return dict(
            id=self.id,
            lat=self.lat,
            lng=self.lng,
        )

    def to_dict(self, current_user=None):
        #get revisions then invert list
        revisions = [{
            'changes': version.changeset,
            'user': version.transaction.user.username,
            'date': version.transaction.issued_at
            } for version in self.versions]
        revisions = revisions[::-1]
        #THIS USER_ID SHIT IS DEFUNCT BECAUSE OF FLASK-LOGIN SESSIONS
        #if user is logged in, include upvote status etc.
        if current_user:
            return dict(id=self.id,
                        name=self.name,
                        created_at=self.created_at,
                        creator_id=self.creator_id,
                        favorited=self.is_favorited(current_user.id),
                        event_tags=[tag.to_dict() for tag in self.event_tags],
                        event_dates=len(self.event_dates),
                        revisions=self.versions.count(),
                        revision_history=revisions
                        )

        else:
            #images_sorted = self.event_images.sort(key=lambda x: x.votes, reverse=True)
            return dict(id=self.id,
                        name=self.name,
                        created_at=self.created_at,
                        creator_id=self.creator_id,
                        event_tags=[tag.to_dict() for tag in self.event_tags],
                        event_dates=len(self.event_dates),
                        revisions=self.versions.count(),
                        revision_history=revisions,
                        )

    def nextEvent(self):
        now = datetime.utcnow()
        eventdate = min(self.event_dates, key=lambda x: abs(x.event_start - now))
        return eventdate

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
