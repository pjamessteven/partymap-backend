from flask_login import current_user
from .model import EventContribution
from pmapi.extensions import db
import pmapi.event_date.controllers as event_dates
import pmapi.event_album.controllers as event_albums


def add_contribution(event_id, creator=current_user, **kwargs):
    text = kwargs.pop("text", None)
    images = kwargs.pop("images", None)
    event_date_id = kwargs.pop("event_date_id", None)

    event_date = None
    album_items = []

    if event_date_id:
        event_date = event_dates.get_event_date_or_404(event_date_id)
        # add images to event_date album
        if images:
            album = event_album.create_album_for_event_date(event_date, images, creator)
            album_items = event_album.add_items_to_album(images, album, creator)

    elif not event_date_id and images:
        # add to default album

    contribution = EventContribution(
        images=album_items,
        text=text,
        event_date_id=event_date_id,
        event_id=event_id,
        creator_id=creator
    )

    db.session.add(contribution)
    current_user.owned_events.append(event)
    db.session.commit()
