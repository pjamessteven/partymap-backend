from datetime import datetime, timedelta
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.hybrid import hybrid_property
import uuid

from pmapi.extensions import db
from pmapi.utils import random_string


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(UUID, primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    to_users = db.relationship(
        "UserNotification", back_populates="notification", cascade="all, delete-orphan"
    )
    notification_type = db.Column(db.String)
    notification_url = db.Column(db.String)


class UserNotification(db.Model):
    __tablename__ = "user_notifications"

    id = db.Column(
        UUID, db.ForeignKey("notifications.id", ondelete="CASCADE"), primary_key=True
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    notification = db.relationship(
        "Notification", back_populates="to_users", lazy="joined", innerjoin=True
    )

    user_id = db.Column(
        UUID, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    user = db.relationship(
        "User", foreign_keys=[user_id], back_populates="notifications"
    )
    read = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return dict(
            id=self.id,
            created_at=self.notification.created_at,
            notification_text=self.notification.notification_text,
            notification_url=self.notification.notification_url,
        )

    def send_email():
        print("send notificaiton email to user")


class EmailAction(db.Model):
    """Table to store password reset requests and email account validations"""

    __tablename__ = "email_actions"

    id = db.Column(db.String(32), primary_key=True, default=lambda: random_string())
    created = db.Column(
        db.DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    user_id = db.Column(
        UUID, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    user = db.relationship("User")
    expires = db.Column(db.DateTime(timezone=True))
    action = db.Column(
        db.Enum(
            "password_reset",
            "email_verify",
            "ilok_verify",
            "account_delete",
            "account_create",
            name="email_action_type",
        )
    )
    extra_data = db.Column(db.String())

    # hybrid property to be used in queries as well as for direct access
    @hybrid_property
    def expired(self):
        # not all actions expire
        if self.expires:
            return self.expires < datetime.utcnow()
        return False

    def __init__(self, action, user=None, extra_data=None, expires=None):
        self.user = user
        self.action = action
        self.extra_data = extra_data
        if not expires:
            if self.action == "password_reset":
                self.expires = datetime.utcnow() + timedelta(hours=24)

            if self.action == "account_delete":
                # account deleting token expires after 5 minutes
                self.expires = datetime.utcnow() + timedelta(minutes=5)
        else:
            self.expires = expires
