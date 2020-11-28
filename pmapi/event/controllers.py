from flask_login import current_user
from .model import Event
from pmapi import exceptions as exc
from pmapi.extensions import db
import pmapi.event_tag.controllers as event_tags
import pmapi.event_image.controllers as event_images
import pmapi.event_date.controllers as event_dates
import pmapi.event_location.controllers as event_locations
import pmapi.user.controllers as users


def get_event_by_id_or_404(id):
    event = get_event_by_id(id)
    if not event:
        msg = "No such event with id {}".format(id)
        raise exc.RecordNotFound(msg)
    return event


def get_event_by_id(id):
    return Event.query.get(id)


def search_events(query):
    query_text = ''
    for word in query.split():
        # this is to formulate a query string like 'twisted:* frequncey:*'
        if word == query.split()[-1]:
            query_text = query_text + (str(word)+str(':*'))
        else:
            query_text = query_text + (str(word)+str(':* & '))

    return Event.query.filter(Event.__ts_vector__.match(
        query_text, postgresql_regconfig='english'))


def get_owned_events(username=None):
    user = None
    if username:
        user = users.get_user_or_404(username)
    elif current_user.id:
        user = users.get_user_or_404(current_user.id)
    else:
        raise exc.LoginRequired()

    return user.owned_events


def add_event(name, description, url, dateTime, rrule, location, tags, images):

    event = Event(name=name,
                  creator_id=current_user.id,
                  default_url=url,
                  description=description)
    db.session.add(event)
    db.session.flush()

    # LOCATION
    event.event_location = event_locations.get_event_location(
        location["place_id"])
    if event.event_location is None:
        event.event_location = event_locations.add_new_event_location(
            **location)

    # TAGS
    event_tags.add_tags_to_event(tags, event)

    # IMAGES
    event_images.add_images_to_event(event, images)

    # DATES
    event_dates.generate_future_event_dates(event, dateTime,
                                            location, rrule, url)

    current_user.owned_events.append(event)

    db.session.commit()
    return event
