from pmapi.application import db
import calendar
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user


# tag is the parent of event
class Tag(db.Model):
    __tablename__ = 'tags'

    tag = db.Column(db.String(20), primary_key=True, nullable=False)
    events_with_tag = db.relationship('EventTag', back_populates="tag")
    created_at = db.Column(db.Integer, default=datetime.utcnow())

    def to_dict(self):
        return dict(text=self.tag,
                    created_at=self.created_at,
                    count=len(self.events_with_tag)
        )



#when adding an event tag, only need to specify votes, tag and event. PKs are automatic. Somehow..
class EventTag(db.Model):
    __tablename__ = 'event_tags'

    tag_id = db.Column(db.String(50), db.ForeignKey('tags.tag'), primary_key=True)
    event_date_id = db.Column(db.Integer, db.ForeignKey('event_dates.id'), primary_key=True)

    tag = db.relationship('Tag', back_populates="events_with_tag")
    event_date = db.relationship('EventDate', back_populates="event_tags")
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.Integer, default=datetime.utcnow())

    status = db.Column(db.SmallInteger, default=1)
    votes = db.Column(db.Integer, default=0)
    hotness = db.Column(db.Float(15,6), default=0.00)

    def to_dict(self):
        tag = self.tag.to_dict()
        return dict(
                text = tag['text'],
                count = tag['count'],
                label = tag['text'] + ' (' + str(tag['count']) + ')',
                )
