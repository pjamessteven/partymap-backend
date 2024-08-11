from datetime import datetime

from sqlalchemy.dialects.postgresql import JSONB, UUID
from pmapi.extensions import db

# from pmapi.favorite_events.model import favorites_association_table


class SuggestedEdit(db.Model):
    __tablename__ = "suggested_edits"
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    creator_id = db.Column(UUID, db.ForeignKey("users.id", name='fk_suggested_edits_creator_id'), nullable=True)
    creator = db.relationship("User", foreign_keys=[creator_id])

    event_id = db.Column(db.Integer, db.ForeignKey("events.id", name='fk_suggested_edits_event_id'), nullable=True)
    event = db.relationship("Event", back_populates="suggestions")
    event_date_id = db.Column(
        db.Integer, db.ForeignKey("event_dates.id", name='fk_suggested_edits_event_date_id'), nullable=True
    )
    event_date = db.relationship("EventDate", back_populates="suggestions")

    artist_id = db.Column(db.Integer, db.ForeignKey("artists.id", name='fk_suggested_edits_artist_id'), nullable=True)
    artist = db.relationship("Artist", back_populates="suggestions")

    status = db.Column(
        db.Enum("approved", "hidden", "pending", name="suggestion_status"),
        default="pending",
    )
    approved = db.Column(db.Boolean, nullable=True)  # remove this column
    approved_by_id = db.Column(UUID, db.ForeignKey("users.id", name='fk_suggested_edits_approved_by_id'), nullable=True)
    approved_by = db.relationship("User", foreign_keys=[approved_by_id])
    approved_at = db.Column(db.DateTime)
    action = db.Column(db.Enum("create", "update", "delete", name="edit_action"))
    object_type = db.Column(db.String)
    kwargs = db.Column(JSONB)
    message = db.Column(db.Text)
