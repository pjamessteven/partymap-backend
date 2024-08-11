from flask import Flask
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
import uuid
from pmapi.extensions import db

app = Flask(__name__)


class Report(db.Model):
    __tablename__ = "reports"

    id = db.Column(UUID, primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    creator_id = db.Column(UUID, db.ForeignKey("users.id", name='fk_reports_creator_id'))
    creator = db.relationship("User", back_populates="created_reports")

    open = db.Column(db.Boolean, default=True)

    message = db.Column(db.Text)
    email = db.Column(db.Text)

    event_id = db.Column(db.Integer, db.ForeignKey("events.id", name='fk_reports_event_id'))
    event = db.relationship("Event", back_populates="reports")

    media_item_id = db.Column(db.Integer, db.ForeignKey("media_items.id", name='fk_reports_media_item_id'))
    media_item = db.relationship("MediaItem", back_populates="reports")

    event_review_id = db.Column(
        db.Integer, db.ForeignKey("event_reviews.id", name='fk_reports_event_review_id'))
    event_review = db.relationship(
        "EventReview", back_populates="reports")
