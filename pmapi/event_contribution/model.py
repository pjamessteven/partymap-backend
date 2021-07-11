import math
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
from sqlalchemy.dialects.postgresql import UUID

from pmapi.extensions import db

event_contribution_upvotes = db.Table(
    "event_contribution_upvotes",
    db.Column("user_id", db.Integer, db.ForeignKey("users.id")),
    db.Column(
        "event_contribution_id", db.Integer, db.ForeignKey("event_contributions.id")
    ),
)

event_contribution_downvotes = db.Table(
    "event_contribution_downvotes",
    db.Column("user_id", db.Integer, db.ForeignKey("users.id")),
    db.Column(
        "event_contribution_id", db.Integer, db.ForeignKey("event_contributions.id")
    ),
)


class EventContribution(db.Model):
    __tablename__ = "event_contributions"

    id = db.Column(UUID, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator_id = db.Column(UUID, db.ForeignKey("users.id"), nullable=False)
    creator = db.relationship("User", back_populates="created_contributions")

    event_id = db.Column(UUID, db.ForeignKey("events.id"), nullable=False)
    event = db.relationship("Event", back_populates="event_contributions")
    event_date_id = db.Column(UUID, db.ForeignKey("event_dates.id"))
    event_date = db.relationship("EventDate", back_populates="contributions")

    text = db.Column(db.Text)
    media_items = db.relationship("MediaItem", back_populates="contribution")

    status = db.Column(db.SmallInteger, default=1)
    score = db.Column(db.Integer, default=0)
    hotness = db.Column(db.Float(15, 6), default=0.00)
    reports = db.relationship("Report", back_populates="event_contribution")

    def to_dict(self):
        return dict(
            id=self.id,
            text=self.text,
            created=self.created_at,
            votes=self.score,
            creator=self.creator.username,
            event_id=self.event_id,
        )

    def get_status(self):
        """
        returns string form of status, 0 = 'dead', 1 = 'alive'
        """
        return self.status

    def get_hotness(self):
        """
        returns the reddit hotness algorithm (votes/(age^1.5))
        """
        order = math.log(
            max(abs(self.score), 1), 10
        )  # Max/abs are not needed in our case
        seconds = self.get_age() - 1134028003
        return round(order + seconds / 45000, 6)

    def set_hotness(self):
        """
        returns the reddit hotness algorithm (votes/(age^1.5))
        """
        self.hotness = self.get_hotness()
        db.session.commit()

    def get_upvoter_ids(self):
        """
        return ids of users who voted this item up
        """
        select = event_contribution_upvotes.select(
            event_contribution_upvotes.c.thread_id == self.id
        )
        rs = db.engine.execute(select)
        ids = rs.fetchall()  # list of tuples
        return ids

    def get_downvoter_ids(self):
        """
        return ids of users who voted this item down
        """
        select = event_contribution_downvotes.select(
            event_contribution_downvotes.c.thread_id == self.id
        )
        rs = db.engine.execute(select)
        ids = rs.fetchall()  # list of tuples
        return ids

    def has_voted(self, user_id):
        """
        did the user vote already?
        will return 1 if upvoted, -1 if downvoted and 0 if not voted.
        """
        select_upvotes = event_contribution_upvotes.select(
            db.and_(
                event_contribution_upvotes.c.user_id == user_id,
                event_contribution_upvotes.c.event_contribution_id == self.id,
            )
        )
        select_downvotes = event_contribution_downvotes.select(
            db.and_(
                event_contribution_downvotes.c.user_id == user_id,
                event_contribution_downvotes.c.event_contribution_id == self.id,
            )
        )
        rs = db.engine.execute(select_upvotes).fetchall()
        rs1 = db.engine.execute(select_downvotes).fetchall()

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
        allow a user to vote on an item. if we have voted already
        (and they are clicking again), this means that they are trying
        to unvote the item, return status of the vote for that user
        """
        already_voted = self.has_voted(user_id)
        vote_status = None
        # if user hasn't already voted
        if already_voted == 0:
            if vote == 1:
                # vote up the item
                db.engine.execute(
                    event_contribution_upvotes.insert(),
                    user_id=user_id,
                    event_contribution_id=self.id,
                )
                self.score = self.score + 1
                vote_status = 1
            elif vote == -1:
                # downvote the item
                db.engine.execute(
                    event_contribution_downvotes.insert(),
                    user_id=user_id,
                    event_contribution_id=self.id,
                )
                self.score = self.score - 1
                vote_status = -1
        # if they have already upvoted
        elif already_voted == 1:
            # and they have selected upvote again
            if vote == 1:
                # unvote the thread
                db.engine.execute(
                    event_contribution_upvotes.delete(
                        db.and_(
                            event_contribution_upvotes.c.user_id == user_id,
                            event_contribution_upvotes.c.event_contribution_id
                            == self.id,
                        )
                    )
                )
                self.score = self.score - 1
                vote_status = -1
            # and they now select downvote instead
            elif vote == -1:
                # unvote the item
                db.engine.execute(
                    event_contribution_upvotes.delete(
                        db.and_(
                            event_contribution_upvotes.c.user_id == user_id,
                            event_contribution_upvotes.c.event_contribution_id
                            == self.id,
                        )
                    )
                )
                self.score = self.score - 1
                # and now add a downvote
                db.engine.execute(
                    event_contribution_downvotes.insert(),
                    user_id=user_id,
                    event_contribution_id=self.id,
                )
                self.score = self.score - 1
                vote_status = -2
        # if they have already downvoted
        elif already_voted == -1:
            # and they select downvote again
            if vote == -1:
                # undownvote the item
                db.engine.execute(
                    event_contribution_downvotes.delete(
                        db.and_(
                            event_contribution_downvotes.c.user_id == user_id,
                            event_contribution_downvotes.c.event_contribution_id
                            == self.id,
                        )
                    )
                )
                self.score = self.score + 1
                vote_status = 1
            elif vote == 1:
                # undownvote the item
                db.engine.execute(
                    event_contribution_downvotes.delete(
                        db.and_(
                            event_contribution_downvotes.c.user_id == user_id,
                            event_contribution_downvotes.c.event_contribution_id
                            == self.id,
                        )
                    )
                )
                self.score = self.score + 1
                # then add an upvote
                db.engine.execute(
                    event_contribution_upvotes.insert(),
                    user_id=user_id,
                    event_contribution_id=self.id,
                )
                self.score = self.score + 1
                vote_status = +2

        db.session.commit()  # for the vote count
        return vote_status
