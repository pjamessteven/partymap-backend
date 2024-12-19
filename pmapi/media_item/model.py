from datetime import datetime
from pmapi.media_item.schemas import generate_filepath
from sqlalchemy.dialects.postgresql import UUID, JSONB

import uuid
from pmapi.extensions import db

"""
media_item_upvotes = db.Table(
    "media_item_upvotes",
    db.Column("user_id", UUID, db.ForeignKey("users.id")),
    db.Column("album_item_id", UUID, db.ForeignKey("album_items.id")),
)

media_item_downvotes = db.Table(
    "media_item_downvotes",
    db.Column("user_id", UUID, db.ForeignKey("users.id")),
    db.Column("album_item_id", UUID, db.ForeignKey("album_items.id")),
)
"""


class MediaItem(db.Model):
    __versioned__ = {'versioning_relations': ['event', 'event_date', 'artist']}
    __tablename__ = "media_items"
    id = db.Column(db.Integer, primary_key=True)
    # can hold flags such as isLineupImage or isEventLogo
    attributes = db.Column(JSONB)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    creator_id = db.Column(UUID, db.ForeignKey("users.id", name='fk_media_items_creator_id')) 
    creator = db.relationship(
        "User", back_populates="created_media_items", foreign_keys=[creator_id])

    caption = db.Column(db.Text)
    type = db.Column(db.Enum("image", "video", name="media_type"))
    position = db.Column(db.Integer)

    thumb_xxs_filename = db.Column(
        db.String, default=None, nullable=True)  # 64x64
    thumb_xs_filename = db.Column(
        db.String, default=None, nullable=True)  # 256x256
    thumb_filename = db.Column(
        db.String, default=None, nullable=False)  # 512x512
    image_med_filename = db.Column(
        db.String, default=None, nullable=True)  # 1024x1024
    image_filename = db.Column(db.String, default=None, nullable=True)

    video_low_filename = db.Column(db.String, default=None, nullable=True)
    video_med_filename = db.Column(db.String, default=None, nullable=True)
    video_high_filename = db.Column(db.String, default=None, nullable=True)
    video_poster_filename = db.Column(db.String, default=None, nullable=True)
    duration = db.Column(db.Integer)  # in seconds
    
    review_id = db.Column(db.Integer, db.ForeignKey("event_reviews.id", name='fk_media_items_review_id'))
    review = db.relationship(
        "EventReview", back_populates="media_items")

    event_id = db.Column(db.Integer, db.ForeignKey("events.id", name='fk_media_items_event_id'), nullable=True)
    event = db.relationship(
        "Event", back_populates="media_items", foreign_keys=[event_id])

    event_date_id = db.Column(db.Integer, db.ForeignKey("event_dates.id", name='fk_media_items_event_date_id'))
    event_date = db.relationship("EventDate", uselist=False)

    artist_id = db.Column(db.Integer, db.ForeignKey("artists.id", name='fk_media_items_artist_id'))
    artist = db.relationship("Artist")

    is_user_avatar = db.relationship(
        "User", back_populates="avatar", uselist=False, primaryjoin="User.avatar_id == MediaItem.id"
    )

    reports = db.relationship("Report", back_populates="media_item")

    @property
    def url(self):
        # return first item as cover image
        return generate_filepath(self, self.image_filename)


    """
    status = db.Column(db.SmallInteger, default=1)

    score = db.Column(db.Integer, default=0)
    hotness = db.Column(db.Float(15, 6), default=0.00) """
