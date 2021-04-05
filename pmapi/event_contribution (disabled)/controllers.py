from flask_login import current_user
from .model import EventContribution
from pmapi.extensions import db


def add_contribution(event, event_images=[], text=None):
    contribution = EventContribution(
        images=event_images,
        text=text,
        creator_id=current_user.id,
        event_id=event.id)

    db.session.add(contribution)
    current_user.owned_events.append(event)
    db.session.commit()
