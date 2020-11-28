import calendar
from datetime import datetime
import os
from flask import current_app
from flask_login import current_user

from pmapi.extensions import db

event_image_upvotes = db.Table('event_image_upvotes',
                               db.Column('user_id', db.Integer,
                                         db.ForeignKey('users.id')),
                               db.Column('event_image_id', db.Integer,
                                         db.ForeignKey('event_images.id'))
                               )

event_image_downvotes = db.Table('event_image_downvotes',
                                 db.Column('user_id', db.Integer,
                                           db.ForeignKey('users.id')),
                                 db.Column('event_image_id', db.Integer,
                                           db.ForeignKey('event_images.id'))
                                 )


class EventImage(db.Model):
    __tablename__ = 'event_images'

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String, default=None, nullable=False)
    thumb_filename = db.Column(db.String, default=None, nullable=False)
    caption = db.Column(db.Text)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    creator = db.relationship('User', back_populates="created_event_images")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    contribution_id = db.Column(db.Integer, db.ForeignKey('event_contributions.id'))
    contribution = db.relationship("EventContribution", back_populates="images")
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'))
    event = db.relationship("Event", back_populates="event_images")
    status = db.Column(db.SmallInteger, default=1)
    # rename to score
    score = db.Column(db.Integer, default=0)
    hotness = db.Column(db.Float(15, 6), default=0.00)
    reports = db.relationship('Report', back_populates="event_image")

    def to_dict(self):
        if self.contribution.event_date:
            path = os.path.join(current_app.config['UPLOADS_URL']+str('event/')+str(
                self.contribution.event.id)+str('/')+str(self.contribution.event_date.id)+'/')
        else:
            path = os.path.join(
                current_app.config['UPLOADS_URL']+str('event/')+str(self.contribution.event.id)+str('/'))

        if current_user.is_authenticated:
            print('ei.todict')
            return dict(id=self.id,
                        caption=self.caption,
                        image_filename=self.filename,
                        image_thumb_url=os.path.join(path, self.thumb_filename),
                        image_url=os.path.join(path, self.filename),
                        created_at=self.created_at,
                        score=self.score,
                        creator=self.creator.username,
                        contribution=self.contribution_id,
                        has_voted=self.has_voted(current_user.id))

        else:
            return dict(id=self.id,
                        caption=self.caption,
                        image_filename=self.filename,
                        image_thumb_url=os.path.join(path, self.thumb_filename),
                        image_url=os.path.join(path, self.filename),
                        created_at=self.created_at,
                        score=self.score,
                        creator=self.creator.username,
                        contribution=self.contribution_id)

    def get_status(self):
        """
        returns string form of status, 0 = 'dead', 1 = 'alive'
        """
        return self.status

    def get_hotness(self):
        """
        returns the reddit hotness algorithm (votes/(age^1.5))
        """
        order = log(max(abs(self.score), 1), 10)  # Max/abs are not needed in our case
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
        select = event_image_upvotes.select(
            event_image_upvotes.c.event_image_id == self.id)
        rs = db.engine.execute(select)
        ids = rs.fetchall()  # list of tuples
        return ids

    def get_downvoter_ids(self):
        """
        return ids of users who voted this item down
        """
        select = event_image_downvotes.select(
            event_image_downvotes.c.event_image_id == self.id)
        rs = db.engine.execute(select)
        ids = rs.fetchall()  # list of tuples
        return ids

    def has_voted(self, user_id):
        """
        did the user vote ? will return 1 if upvoted, -1 if downvoted and 0 if not voted.
        """
        select_upvotes = event_image_upvotes.select(
            db.and_(
                event_image_upvotes.c.user_id == user_id,
                event_image_upvotes.c.event_image_id == self.id
            )
        )
        select_downvotes = event_image_downvotes.select(
            db.and_(
                event_image_downvotes.c.user_id == user_id,
                event_image_downvotes.c.event_image_id == self.id
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
        # if user hasn't  voted
        if _voted == 0:
            if vote == 1:
                # vote up the item
                db.engine.execute(
                    event_image_upvotes.insert(),
                    user_id=user_id,
                    event_image_id=self.id
                )
                self.score = self.score + 1
                vote_status = 1
            elif vote == -1:
                # downvote the item
                db.engine.execute(
                    event_image_downvotes.insert(),
                    user_id=user_id,
                    event_image_id=self.id
                )
                self.score = self.score - 1
                vote_status = -1
            else:
                return None
        # if they have  upvoted
        elif _voted == 1:
            # and they have selected upvote again
            if vote == 1:
                # unvote the item
                db.engine.execute(
                    event_image_upvotes.delete(
                        db.and_(
                            event_image_upvotes.c.user_id == user_id,
                            event_image_upvotes.c.event_image_id == self.id
                        )
                    )
                )
                self.score = self.score - 1
                vote_status = -1
            # and they now select downvote instead
            elif vote == -1:
                # unvote the item
                db.engine.execute(
                    event_image_upvotes.delete(
                        db.and_(
                            event_image_upvotes.c.user_id == user_id,
                            event_image_upvotes.c.event_image_id == self.id
                        )
                    )
                )
                self.score = self.score - 1
                # and now add a downvote
                db.engine.execute(
                    event_image_downvotes.insert(),
                    user_id=user_id,
                    event_image_id=self.id
                )
                self.score = self.score - 1
                vote_status = -2
            else:
                return None
        # if they have  downvoted
        elif _voted == -1:
            # and they select downvote again
            if vote == -1:
                # undownvote the item
                db.engine.execute(
                    event_image_downvotes.delete(
                        db.and_(
                            event_image_downvotes.c.user_id == user_id,
                            event_image_downvotes.c.event_image_id == self.id
                        )
                    )
                )
                self.score = self.score + 1
                vote_status = 1
            elif vote == 1:
                # undownvote the item
                db.engine.execute(
                    event_image_downvotes.delete(
                        db.and_(
                            event_image_downvotes.c.user_id == user_id,
                            event_image_downvotes.c.event_image_id == self.id
                        )
                    )
                )
                self.score = self.score + 1
                # then add an upvote
                db.engine.execute(
                    event_image_upvotes.insert(),
                    user_id=user_id,
                    event_image_id=self.id
                )
                self.score = self.score + 1
                vote_status = +2
            else:
                return None
        db.session.commit()  # for the vote count
        return vote_status
