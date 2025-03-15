from datetime import datetime
from pmapi.media_item.schemas import generate_filepath, generate_local_filepath
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import event
import os
import uuid
from pmapi.extensions import db
import logging


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

    def delete_files(self):
        """Delete all associated media files"""
        file_fields = [
            'thumb_xxs_filename', 'thumb_xs_filename', 'thumb_filename',
            'image_med_filename', 'image_filename', 'video_low_filename',
            'video_med_filename', 'video_high_filename', 'video_poster_filename'
        ]
        
        for field in file_fields:
            filename = getattr(self, field)
            if filename:
                file_path = generate_local_filepath(self, filename)
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except OSError as e:
                    logging.error(f"Error deleting file {file_path}: {str(e)}")

@event.listens_for(MediaItem, 'after_delete')
def delete_media_files(mapper, connection, target):
    """SQLAlchemy event listener to delete files after model deletion"""
    target.delete_files()
