from flask_login import current_user
from .model import Event
from pmapi import exceptions as exc
from pmapi.extensions import db
import pmapi.event_tag.controllers as event_tags
import pmapi.event_image.controllers as event_images
import pmapi.event_date.controllers as event_dates
import pmapi.event_location.controllers as event_locations
from pmapi.common.controllers import paginated_results


def get_event_by_id_or_404(id):
    event = get_event_by_id(id)
    if not event:
        msg = "No such event with id {}".format(id)
        raise exc.RecordNotFound(msg)
    return event


def get_event_by_id(id):
    return Event.query.get(id)


def search_events(**kwargs):
    query = db.session.query(Event)

    if "query" in kwargs:
        query = kwargs.pop("query")
        query_text = ""
        for word in query.split():
            # this is to formulate a query string like 'twisted:* frequncey:*'
            if word == query.split()[-1]:
                query_text = query_text + (str(word) + str(":*"))
            else:
                query_text = query_text + (str(word) + str(":* & "))

        query = query.filter(
            Event.__ts_vector__.match(query_text, postgresql_regconfig="english")
        )
    return paginated_results(Event, query, **kwargs)


def add_event(**kwargs):

    name = kwargs.pop("name")
    description = kwargs.pop("description")
    location = kwargs.pop("location")
    dateTime = kwargs.pop("dateTime")
    rrule = kwargs.pop("rrule")
    url = kwargs.pop("url", None)
    tags = kwargs.pop("tags", None)
    images = kwargs.pop("images", None)

    event = Event(
        name=name, creator_id=current_user.id, default_url=url, description=description
    )
    db.session.add(event)
    db.session.flush()

    if tags:
        event_tags.add_tags_to_event(tags, event)

    if images:
        event_images.add_images_to_event(event, images)

    # LOCATION
    event.event_location = event_locations.get_event_location(location["place_id"])
    if event.event_location is None:
        event.event_location = event_locations.add_new_event_location(**location)

    # DATES
    event_dates.generate_future_event_dates(event, dateTime, location, rrule, url)

    db.session.commit()
    return event


def update_event(event_id, **kwargs):
    event = get_event_by_id_or_404(event_id)

    rrule = kwargs.get("rrule")
    url = kwargs.get("url")
    location = kwargs.get("location")
    dateTime = kwargs.get("dateTime")
    description = kwargs.get("description")
    tags = kwargs.get("tags")
    images = kwargs.get("images")

    if description:
        event.description = description
        # activity = Activity(verb=u"update", object=event)
        # create_notification('UPDATE EVENT', activity, event.followers)
        # db.session.add(activity)

    if rrule is not None and rrule is False:
        db.session.delete(event.rrule)

    if dateTime and location and rrule:
        return event_dates.generate_future_event_dates(
            event, dateTime, location, rrule, url
        )

    if tags:
        event_tags.add_tags_to_event(tags, event)

    if images:
        event_images.add_images_to_event(event, images)

    db.session.commit()

    return event
