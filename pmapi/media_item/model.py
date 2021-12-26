from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
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
    __versioned__ = {}
    __tablename__ = "media_items"

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    creator_id = db.Column(UUID, db.ForeignKey("users.id"))
    creator = db.relationship("User", back_populates="created_media_items")

    caption = db.Column(db.Text)
    type = db.Column(db.Enum("image", "video", name="media_type"))
    position = db.Column(db.Integer)

    thumb_xs_filename = db.Column(db.String, default=None, nullable=True)  # 256x256
    thumb_filename = db.Column(db.String, default=None, nullable=False)  # 512x512
    image_med_filename = db.Column(db.String, default=None, nullable=True)  # 1024x1024
    image_filename = db.Column(db.String, default=None, nullable=True)

    video_low_filename = db.Column(db.String, default=None, nullable=True)
    video_med_filename = db.Column(db.String, default=None, nullable=True)
    video_high_filename = db.Column(db.String, default=None, nullable=True)
    video_poster_filename = db.Column(db.String, default=None, nullable=True)
    duration = db.Column(db.Integer)  # in seconds

    contribution_id = db.Column(UUID, db.ForeignKey("event_contributions.id"))
    contribution = db.relationship("EventContribution", back_populates="media_items")

    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=True)
    event = db.relationship("Event", back_populates="media_items")

    event_date_id = db.Column(db.Integer, db.ForeignKey("event_dates.id"))
    event_date = db.relationship("EventDate", uselist=False)

    artist_id = db.Column(db.Integer, db.ForeignKey("artists.id"))
    artist = db.relationship("Artist")

    """
    status = db.Column(db.SmallInteger, default=1)

    score = db.Column(db.Integer, default=0)
    hotness = db.Column(db.Float(15, 6), default=0.00) """
