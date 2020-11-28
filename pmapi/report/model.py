from datetime import datetime
from sqlalchemy import ForeignKeyConstraint

from pmapi.extensions import db


class Report(db.Model):
    __tablename__ = 'reports'
    __table_args__ = (
        ForeignKeyConstraint(['event_date_id', 'event_artist_artist_name'],
                             ['event_artists.event_date_id', 'event_artists.artist_name']),
        ForeignKeyConstraint(['event_id', 'event_tag_tag_id'],
                             ['event_tags.event_id', 'event_tags.tag_id']),
        {})

    id = db.Column(db.Integer, primary_key=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    creator = db.relationship('User', backref="reports_submitted",
                              foreign_keys="[Report.creator_id]")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    creator_ip = db.Column(db.String(50))
    reason_text = db.Column(db.Text)

    # user who created content has the report against their name
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', backref="reports_against",
                           foreign_keys="[Report.user_id]")
    # report types
    event = db.relationship('Event', back_populates="reports")
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'))
    event_date = db.relationship('EventDate', back_populates="reports")
    event_date_id = db.Column(db.Integer, db.ForeignKey('event_dates.id'))
    event_contribution = db.relationship('EventContribution', back_populates="reports")
    event_contribution_id = db.Column(db.Integer, db.ForeignKey('event_contributions.id'))
    event_image = db.relationship('EventImage', back_populates="reports")
    event_image_id = db.Column(db.Integer, db.ForeignKey('event_images.id'))
    event_artist_artist_name = db.Column(db.String)
    event_tag_tag_id = db.Column(db.String)
