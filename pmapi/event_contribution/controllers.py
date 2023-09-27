from flask_login import current_user
from .model import EventContribution
from pmapi.extensions import db
import pmapi.event.controllers as events
import pmapi.event_date.controllers as event_dates
import pmapi.media_item.controllers as media_items
import pmapi.exceptions as exc


def get_contribution(id):
    return EventContribution.query.get(id)


def add_contribution(event_id, creator=current_user, **kwargs):

    text = kwargs.pop("text", None)
    media = kwargs.pop("media_items", None)
    event_date_id = kwargs.pop("event_date_id", None)
    rating = kwargs.pop("rating", None)

    event = events.get_event_or_404(event_id)

    event_date = None

    if not rating:
        raise exc.InvalidAPIRequest(
            "Rating required"
        )

    if event_date_id:
        event_date = event_dates.get_event_date_or_404(event_date_id)

    # add images to event_date album
    items = []
    if media:
        items = media_items.add_media_to_event(
            media, event, event_date, creator)

    contribution = EventContribution(
        media_items=items,
        text=text,
        event_date_id=event_date_id,
        event_id=event_id,
        creator_id=creator.get_id(),
        rating=rating
    )

    db.session.add(contribution)
    db.session.commit()

    return contribution
