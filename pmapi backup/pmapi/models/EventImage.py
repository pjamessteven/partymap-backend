from pmapi.application import db
import calendar
from datetime import datetime
import os
from flask import current_app
from flask_login import current_user

eventimage_upvotes = db.Table('eventimage_upvotes',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('eventimage_id', db.Integer, db.ForeignKey('eventimages.id'))
)

eventimage_downvotes = db.Table('eventimage_downvotes',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('eventimage_id', db.Integer, db.ForeignKey('eventimages.id'))
)


class EventImage(db.Model):
    __tablename__ = 'eventimages'

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String, default=None, nullable=False)
    thumb_filename = db.Column(db.String, default=None, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'))
    created_at = db.Column(db.Integer, default=datetime.utcnow())
    status = db.Column(db.SmallInteger, default=1)
    votes = db.Column(db.Integer, default=0)
    hotness = db.Column(db.Float(15,6), default=0.00)


    def to_dict(self):

        if current_user.is_authenticated:
            return dict(id=self.id,
                        image_filename=self.filename,
                        image_thumb_url=os.path.join(current_app.config['UPLOADS_URL'], self.thumb_filename),
                        image_url=os.path.join(current_app.config['UPLOADS_URL'], self.filename),
                        created_at=self.created_at,
                        votes=self.votes,
                        user_id=self.user_id,
                        event_id=self.event_id,
                        has_voted=self.has_voted(current_user.id))

        else:
            return dict(id=self.id,
                        image_filename=self.filename,
                        image_thumb_url=os.path.join(current_app.config['UPLOADS_URL'], self.thumb_filename),
                        image_url=os.path.join(current_app.config['UPLOADS_URL'], self.filename),
                        created_at=self.created_at,
                        votes=self.votes,
                        user_id=self.user_id,
                        event_id=self.event_id)


    def get_status(self):
        """
        returns string form of status, 0 = 'dead', 1 = 'alive'
        """
        return self.status

    def get_hotness(self):
        """
        returns the reddit hotness algorithm (votes/(age^1.5))
        """
        order = log(max(abs(self.votes), 1), 10) # Max/abs are not needed in our case
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
        select = eventimage_upvotes.select(eventimage_upvotes.c.eventimage_id==self.id)
        rs = db.engine.execute(select)
        ids = rs.fetchall() # list of tuples
        return ids

    def get_downvoter_ids(self):
        """
        return ids of users who voted this item down
        """
        select = eventimage_downvotes.select(eventimage_downvotes.c.eventimage_id==self.id)
        rs = db.engine.execute(select)
        ids = rs.fetchall() # list of tuples
        return ids

    def has_voted(self, user_id):
        """
        did the user vote ? will return 1 if upvoted, -1 if downvoted and 0 if not voted.
        """
        select_upvotes = eventimage_upvotes.select(
                db.and_(
                    eventimage_upvotes.c.user_id == user_id,
                    eventimage_upvotes.c.eventimage_id == self.id
                )
        )
        select_downvotes = eventimage_downvotes.select(
                db.and_(
                    eventimage_downvotes.c.user_id == user_id,
                    eventimage_downvotes.c.eventimage_id == self.id
                )
        )
        rs = db.engine.execute(select_upvotes).fetchall()
        rs1 = db.engine.execute(select_downvotes).fetchall()
        print(len(rs))
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
        #if user hasn't  voted
        if _voted==0:
            if vote == 1:
                # vote up the item
                db.engine.execute(
                    eventimage_upvotes.insert(),
                    user_id   = user_id,
                    eventimage_id = self.id
                    )
                self.votes = self.votes + 1
                vote_status = 1
            elif vote == -1:
                #downvote the item
                db.engine.execute(
                    eventimage_downvotes.insert(),
                    user_id   = user_id,
                    eventimage_id = self.id
                    )
                self.votes = self.votes - 1
                vote_status = -1
            else:
                return None
        #if they have  upvoted
        elif _voted==1:
            #and they have selected upvote again
            if vote==1:
                # unvote the item
                db.engine.execute(
                    eventimage_upvotes.delete(
                        db.and_(
                            eventimage_upvotes.c.user_id == user_id,
                            eventimage_upvotes.c.eventimage_id == self.id
                        )
                    )
                )
                self.votes = self.votes - 1
                vote_status = -1
            #and they now select downvote instead
            elif vote==-1:
                # unvote the item
                db.engine.execute(
                    eventimage_upvotes.delete(
                        db.and_(
                            eventimage_upvotes.c.user_id == user_id,
                            eventimage_upvotes.c.eventimage_id == self.id
                        )
                    )
                )
                self.votes = self.votes - 1
                #and now add a downvote
                db.engine.execute(
                    eventimage_downvotes.insert(),
                    user_id   = user_id,
                    eventimage_id = self.id
                    )
                self.votes = self.votes - 1
                vote_status = -2
            else:
                return None
        #if they have  downvoted
        elif _voted==-1:
            #and they select downvote again
            if vote==-1:
                # undownvote the item
                db.engine.execute(
                    eventimage_downvotes.delete(
                        db.and_(
                            eventimage_downvotes.c.user_id == user_id,
                            eventimage_downvotes.c.eventimage_id == self.id
                        )
                    )
                )
                self.votes = self.votes + 1
                vote_status = 1
            elif vote==1:
                #undownvote the item
                db.engine.execute(
                    eventimage_downvotes.delete(
                        db.and_(
                            eventimage_downvotes.c.user_id == user_id,
                            eventimage_downvotes.c.eventimage_id == self.id
                        )
                    )
                )
                self.votes = self.votes + 1
                #then add an upvote
                db.engine.execute(
                    eventimage_upvotes.insert(),
                    user_id   = user_id,
                    eventimage_id = self.id
                    )
                self.votes = self.votes + 1
                vote_status = +2
            else:
                return None
        db.session.commit() # for the vote count
        return vote_status
