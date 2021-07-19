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
    creator_id = db.Column(UUID, db.ForeignKey("users.id"))
    creator = db.relationship("User", back_populates="created_reports")

    open = db.Column(db.Boolean, default=True)

    description = db.Column(db.Text)

    event_contribution_id = db.Column(UUID, db.ForeignKey("event_contributions.id"))
    event_contribution = db.relationship("EventContribution", back_populates="reports")

    event_id = db.Column(UUID, db.ForeignKey("events.id"))
    event = db.relationship("Event", back_populates="reports")

    media_item_id = db.Column(UUID, db.ForeignKey("media_items.id"))
    media_item = db.relationship("MediaItem", back_populates="reports")
