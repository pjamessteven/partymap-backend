from datetime import datetime
from sqlalchemy import ForeignKeyConstraint

from pmapi.extensions import db


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    to_users = db.relationship('UserNotification',
                               back_populates='notification',
                               cascade='all, delete-orphan'
                               )
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    notification_type = db.Column(db.String)
    # TYPES: 'UPDATE EVENT' 'VOTE PHOTO'
    notification_url = db.Column(db.String)


class UserNotification(db.Model):
    __tablename__ = 'user_notifications'

    id = db.Column(db.Integer,
                   db.ForeignKey('notifications.id', ondelete='CASCADE'),
                   primary_key=True)
    notification = db.relationship('Notification',

                                   back_populates='to_users',
                                   lazy='joined', innerjoin=True)

    user_id = db.Column(db.Integer,
                        db.ForeignKey('users.id', ondelete='CASCADE'),
                        primary_key=True)
    user = db.relationship('User',
                           foreign_keys=[user_id],
                           back_populates='notifications')
    read = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return dict(
            id=self.id,
            created_at=self.notification.created_at,
            notification_text=self.notification.notification_text,
            notification_url=self.notification.notification_url
        )

    def send_email():
        print('send notificaiton email to user')
