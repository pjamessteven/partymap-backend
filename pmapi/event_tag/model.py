import calendar
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
from sqlalchemy import Index, func, cast
from sqlalchemy.sql import func
from sqlalchemy.dialects import postgresql
from sqlalchemy import ForeignKeyConstraint, UniqueConstraint

from pmapi.extensions import db


def create_tsvector(*args):
    exp = args[0]
    for e in args[1:]:
        exp += ' ' + e
    return func.to_tsvector('english', exp)


event_tag_upvotes = db.Table('event_tag_upvotes',
                             db.Column('user_id', db.Integer, db.ForeignKey(
                                 'users.id'), primary_key=True),
                             db.Column('tag', db.String(20), db.ForeignKey(
                                 'tags.tag'), primary_key=True),
                             db.Column('event_id', db.Integer, db.ForeignKey(
                                 'events.id'), primary_key=True),
                             )

event_tag_downvotes = db.Table('event_tag_downvotes',
                               db.Column('user_id', db.Integer, db.ForeignKey(
                                   'users.id'), primary_key=True),
                               db.Column('tag', db.String(20), db.ForeignKey(
                                   'tags.tag'), primary_key=True),
                               db.Column('event_id', db.Integer, db.ForeignKey(
                                   'events.id'), primary_key=True),
                               )


# tag is the parent of event
class Tag(db.Model):
    __tablename__ = 'tags'

    tag = db.Column(db.String(20), primary_key=True, nullable=False)
    events_with_tag = db.relationship('EventTag', back_populates="tag")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __ts_vector__ = create_tsvector(
        cast(func.coalesce(tag, ''), postgresql.TEXT)
    )

    # this is an index for searching artists
    __table_args__ = (
        Index(
            'idx_events_fts',
            __ts_vector__,
            postgresql_using='gin'
        ),
    )

    def to_dict(self):
        return dict(value=self.tag,
                    label=self.tag,
                    type="tag")

    def to_dict_count(self):
        eventids = []
        return dict(value=self.tag,
                    label=self.tag,
                    count=len(self.events_with_tag),
                    type="tag")

# when adding an event tag, only need to specify votes, tag and event. PKs are automatic. Somehow..


class EventTag(db.Model):
    __tablename__ = 'event_tags'

    tag_id = db.Column(db.String(20), db.ForeignKey('tags.tag'), primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), primary_key=True)

    tag = db.relationship('Tag', back_populates="events_with_tag")
    event = db.relationship('Event', back_populates="event_tags")
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    creator = db.relationship('User', back_populates="created_event_tags")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    reports = db.relationship('Report', backref="event_tag")
    status = db.Column(db.SmallInteger, default=1)
    votes = db.Column(db.Integer, default=0)
    hotness = db.Column(db.Float(15, 6), default=0.00)

    def to_dict(self):

        if current_user.is_authenticated:
            return dict(value=self.tag_id,
                        label=self.tag_id,
                        score=self.votes,
                        creator=self.creator.username,
                        type="tag",
                        has_voted=self.has_voted(current_user.id))
        else:
            return dict(value=self.tag_id,
                        label=self.tag_id,
                        score=self.votes,
                        creator=self.creator.username,
                        type="tag")

    def minified(self):
        print('ed.minified')
        return dict(value=self.tag_id,
                    label=self.tag_id,
                    type="tag")

    def get_status(self):
        """
        returns string form of status, 0 = 'dead', 1 = 'alive'
        """
        return self.status

    def get_hotness(self):
        """
        returns the reddit hotness algorithm (votes/(age^1.5))
        """
        order = log(max(abs(self.votes), 1), 10)  # Max/abs are not needed in our case
        seconds = self.get_age() - 1134028003
        return round(order + seconds / 45000, 6)

    def set_hotness(self):
        """
        returns the reddit hotness algorithm (votes/(age^1.5))
        """
        self.hotness = self.get_hotness()
        db.session.commit()

    def pretty_date(self):
        """
        returns a humanized version of the raw age of this item,
        eg: 34 minutes ago versus 2040 seconds ago.
        """
        return utils.pretty_date(self.created_at)

    def get_upvoter_ids(self):
        """
        return ids of users who voted this item up
        """
        select = event_tag_upvotes.select(db.and_(
            event_tag_upvotes.c.tag == self.tag_id,
            event_tag_upvotes.c.event_id == self.event_id
        ))
        rs = db.engine.execute(select)
        ids = rs.fetchall()  # list of tuples
        return ids

    def get_downvoter_ids(self):
        """
        return ids of users who voted this item down
        """
        select = event_tag_downvotes.select(db.and_(
            event_tag_downvotes.c.tag == self.tag_id,
            event_tag_downvotes.c.event_id == self.event_id
        ))
        rs = db.engine.execute(select)
        ids = rs.fetchall()  # list of tuples
        return ids

    def has_voted(self, user_id):
        """
        did the user vote ? will return 1 if upvoted, -1 if downvoted and 0 if not voted.
        """
        select_upvotes = event_tag_upvotes.select(
            db.and_(
                event_tag_upvotes.c.user_id == user_id,
                event_tag_upvotes.c.tag == self.tag_id,
                event_tag_upvotes.c.event_id == self.event_id)
        )
        select_downvotes = event_tag_downvotes.select(
            db.and_(
                event_tag_downvotes.c.user_id == user_id,
                event_tag_downvotes.c.tag == self.tag_id,
                event_tag_downvotes.c.event_id == self.event_id)
        )
        rs = db.engine.execute(select_upvotes).fetchall()
        rs1 = db.engine.execute(select_downvotes).fetchall()
        print(len(rs))
        print('has voted?')
        if len(rs) > 0:
            print("has upvoted")
            return 1
        elif len(rs1) > 0:
            print("has downvoted")
            return -1
        else:
            print("has not voted")
            return 0

    def vote(self, user_id, vote):
        """
        allow a user to vote on an item. if we have voted
        (and they are clicking again), this means that they are trying
        to unvote the item, return status of the vote for that user
        """
        _voted = self.has_voted(user_id)
        vote_status = None
        # if user hasn't  voted
        if _voted == 0:
            if vote == 1:
                # vote up the item
                db.engine.execute(
                    event_tag_upvotes.insert(),
                    user_id=user_id,
                    tag=self.tag_id,
                    event_id=self.event_id
                )
                self.votes = self.votes + 1
                vote_status = 1
            elif vote == -1:
                # downvote the item
                db.engine.execute(
                    event_tag_downvotes.insert(),
                    user_id=user_id,
                    tag=self.tag_id,
                    event_id=self.event_id
                )
                self.votes = self.votes - 1
                vote_status = -1
            else:
                return None
        # if they have  upvoted
        elif _voted == 1:
            # and they have selected upvote again
            if vote == 1:
                # unvote the item
                db.engine.execute(
                    event_tag_upvotes.delete(
                        db.and_(
                            event_tag_upvotes.c.user_id == user_id,
                            event_tag_upvotes.c.tag == self.tag_id,
                            event_tag_upvotes.c.event_id == self.event_id
                        )
                    )
                )
                self.votes = self.votes - 1
                vote_status = -1
            # and they now select downvote instead
            elif vote == -1:
                # unvote the item
                db.engine.execute(
                    event_tag_upvotes.delete(
                        db.and_(
                            event_tag_upvotes.c.user_id == user_id,
                            event_tag_upvotes.c.tag == self.tag_id,
                            event_tag_upvotes.c.event_id == self.event_id
                        )
                    )
                )
                self.votes = self.votes - 1
                # and now add a downvote
                db.engine.execute(
                    event_tag_downvotes.insert(),
                    user_id=user_id,
                    tag=self.tag_id,
                    event_id=self.event_id
                )
                self.votes = self.votes - 1
                vote_status = -2
            else:
                return None
        # if they have  downvoted
        elif _voted == -1:
            # and they select downvote again
            if vote == -1:
                # undownvote the item
                db.engine.execute(
                    event_tag_downvotes.delete(
                        db.and_(
                            event_tag_downvotes.c.user_id == user_id,
                            event_tag_downvotes.c.tag == self.tag_id,
                            event_tag_downvotes.c.event_id == self.event_id
                        )
                    )
                )
                self.votes = self.votes + 1
                vote_status = 1
            elif vote == 1:
                # undownvote the item
                db.engine.execute(
                    event_tag_downvotes.delete(
                        db.and_(
                            event_tag_downvotes.c.user_id == user_id,
                            event_tag_downvotes.c.tag == self.tag_id,
                            event_tag_downvotes.c.event_id == self.event_id
                        )
                    )
                )
                self.votes = self.votes + 1
                # then add an upvote
                db.engine.execute(
                    event_tag_upvotes.insert(),
                    user_id=user_id,
                    tag=self.tag_id,
                    event_id=self.event_id
                )
                self.votes = self.votes + 1
                vote_status = +2
            else:
                return None
        db.session.commit()  # for the vote count
        return vote_status
