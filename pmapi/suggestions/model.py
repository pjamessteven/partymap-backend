from datetime import datetime

from sqlalchemy.dialects.postgresql import JSONB, UUID

from pmapi.extensions import db

# from pmapi.favorite_events.model import favorites_association_table


class SuggestedEdit(db.Model):
    __tablename__ = "suggested_edits"
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)
    event = db.relationship("Event", back_populates="suggestions")
    event_date_id = db.Column(
        db.Integer, db.ForeignKey("event_dates.id"), nullable=True
    )
    event_date = db.relationship("EventDate", back_populates="suggestions")
    approved = db.Column(db.Boolean, nullable=True)
    approved_by = db.relationship("User")
    approved_by_id = db.Column(UUID, db.ForeignKey("users.id"), nullable=True)
    approved_at = db.Column(db.DateTime)
    action = db.Column(db.Enum("create", "update", "delete", name="edit_action"))
    object_type = db.Column(db.String)
    kwargs = db.Column(JSONB)
    message = db.Column(db.Text)
