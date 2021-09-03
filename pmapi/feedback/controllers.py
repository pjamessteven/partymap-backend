from flask_login import current_user

from pmapi.mail.controllers import (
    send_feedback_notification_email,
)
from pmapi.extensions import db

from .model import Feedback


def create_feedback(**kwargs):
    if current_user.is_authenticated:
        creator = current_user
    else:
        creator = None
    message = kwargs.pop("message", None)
    contact_email = kwargs.pop("contact_email", None)

    feedback = Feedback(creator=creator, message=message, contact_email=contact_email)
    db.session.add(feedback)
    db.session.commit()
    send_feedback_notification_email(feedback.id, message, contact_email, creator)
