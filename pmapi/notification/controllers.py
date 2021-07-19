from .model import Notification, UserNotification
from pmapi.extensions import db


def create_notification(notification_type, activity, to_users):

    notification = Notification(notification_type=notification_type,
                                activity=activity,
                                url=activity.object.get_url())
    db.session.add(notification)

    for user in to_users:
        un = UserNotification(notification=notification, user=user)
        db.session.add(un)

    db.session.commit()
