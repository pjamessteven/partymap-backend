import math
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID, HSTORE
import uuid
from sqlalchemy_utils import TranslationHybrid
from flask_babel import get_locale
from pmapi.extensions import db
from sqlalchemy.ext.mutable import MutableDict

translation_hybrid = TranslationHybrid(
    current_locale=get_locale,
    default_locale='en'
)
event_review_upvotes = db.Table(
    "event_review_upvotes",
    db.Column("user_id", UUID, db.ForeignKey("users.id", name='fk_event_review_upvotes_user_id')),
    db.Column("event_review_id", db.Integer,
              db.ForeignKey("event_reviews.id", name='fk_event_review_upvotes_event_review_id')),
)

event_review_downvotes = db.Table(
    "event_review_downvotes",
    db.Column("user_id", UUID, db.ForeignKey("users.id", name='fk_event_review_downvotes_user_id')),
    db.Column("event_review_id", db.Integer,
              db.ForeignKey("event_reviews.id", name='fk_event_review_downvotes_event_review_id')),
)


class EventReview(db.Model):
    __tablename__ = "event_reviews"
    __versioned__ = {'versioning_relations': ['event', 'event_date']}

    id = db.Column(db.Integer, primary_key=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator_id = db.Column(UUID, db.ForeignKey("users.id", name='fk_event_reviews_creator_id'), nullable=False)
    creator = db.relationship("User", back_populates="created_reviews")

    event_id = db.Column(db.Integer, db.ForeignKey(
        "events.id", name='fk_event_reviews_event_id'), nullable=False)
    event = db.relationship("Event", back_populates="event_reviews")
    event_date_id = db.Column(db.Integer, db.ForeignKey("event_dates.id", name='fk_event_reviews_event_date_id'))
    event_date = db.relationship("EventDate", back_populates="reviews")

    rating = db.Column(db.Integer)

    text = db.Column(db.Text)
    text_translations = db.Column(MutableDict.as_mutable(HSTORE))
    text_t = translation_hybrid(text_translations)

    media_items = db.relationship("MediaItem", back_populates="review")

    score = db.Column(db.Integer, default=0)

    reports = db.relationship("Report", back_populates="event_review")

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
        select = event_review_upvotes.select(
            event_review_upvotes.c.thread_id == self.id
        )
        rs = db.engine.execute(select)
        ids = rs.fetchall()  # list of tuples
        return ids

    def get_downvoter_ids(self):
        """
        return ids of users who voted this item down
        """
        select = event_review_downvotes.select(
            event_review_downvotes.c.thread_id == self.id
        )
        rs = db.engine.execute(select)
        ids = rs.fetchall()  # list of tuples
        return ids

    def has_voted(self, user_id):
        """
        did the user vote already?
        will return 1 if upvoted, -1 if downvoted and 0 if not voted.
        """
        select_upvotes = event_review_upvotes.select(
            db.and_(
                event_review_upvotes.c.user_id == user_id,
                event_review_upvotes.c.event_review_id == self.id,
            )
        )
        select_downvotes = event_review_downvotes.select(
            db.and_(
                event_review_downvotes.c.user_id == user_id,
                event_review_downvotes.c.event_review_id == self.id,
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
                    event_review_upvotes.insert(),
                    user_id=user_id,
                    event_review_id=self.id,
                )
                self.score = self.score + 1
                vote_status = 1
            elif vote == -1:
                # downvote the item
                db.engine.execute(
                    event_review_downvotes.insert(),
                    user_id=user_id,
                    event_review_id=self.id,
                )
                self.score = self.score - 1
                vote_status = -1
        # if they have already upvoted
        elif already_voted == 1:
            # and they have selected upvote again
            if vote == 1:
                # unvote the thread
                db.engine.execute(
                    event_review_upvotes.delete(
                        db.and_(
                            event_review_upvotes.c.user_id == user_id,
                            event_review_upvotes.c.event_review_id
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
                    event_review_upvotes.delete(
                        db.and_(
                            event_review_upvotes.c.user_id == user_id,
                            event_review_upvotes.c.event_review_id
                            == self.id,
                        )
                    )
                )
                self.score = self.score - 1
                # and now add a downvote
                db.engine.execute(
                    event_review_downvotes.insert(),
                    user_id=user_id,
                    event_review_id=self.id,
                )
                self.score = self.score - 1
                vote_status = -2
        # if they have already downvoted
        elif already_voted == -1:
            # and they select downvote again
            if vote == -1:
                # undownvote the item
                db.engine.execute(
                    event_review_downvotes.delete(
                        db.and_(
                            event_review_downvotes.c.user_id == user_id,
                            event_review_downvotes.c.event_review_id
                            == self.id,
                        )
                    )
                )
                self.score = self.score + 1
                vote_status = 1
            elif vote == 1:
                # undownvote the item
                db.engine.execute(
                    event_review_downvotes.delete(
                        db.and_(
                            event_review_downvotes.c.user_id == user_id,
                            event_review_downvotes.c.event_review_id
                            == self.id,
                        )
                    )
                )
                self.score = self.score + 1
                # then add an upvote
                db.engine.execute(
                    event_review_upvotes.insert(),
                    user_id=user_id,
                    event_review_id=self.id,
                )
                self.score = self.score + 1
                vote_status = +2

        db.session.commit()  # for the vote count
        return vote_status
