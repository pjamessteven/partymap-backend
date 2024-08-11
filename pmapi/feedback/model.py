from flask import Flask
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
import uuid
from pmapi.extensions import db

app = Flask(__name__)


class Feedback(db.Model):
    __tablename__ = "feedbacks"

    id = db.Column(UUID, primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    creator_id = db.Column(UUID, db.ForeignKey("users.id"), name='fk_feedbacks_creator_id')
    creator = db.relationship("User", back_populates="created_feedback")

    message = db.Column(db.Text)
    contact_email = db.Column(db.Text)
