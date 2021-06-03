from .model import Event, Rrule
from pmapi import exceptions as exc
from pmapi.extensions import db
import pmapi.event_tag.controllers as event_tags
import pmapi.event_album.controllers as event_images
import pmapi.event_date.controllers as event_dates
import pmapi.event_location.controllers as event_locations
from pmapi.common.controllers import paginated_results


def get_event_or_404(id):
    event = get_event(id)
    if not event or event.deleted:
        msg = "No such event with id {}".format(id)
        raise exc.RecordNotFound(msg)
    return event


def get_event(id):
    event = Event.query.get(str(id))  # uuid to string
    if event and not event.deleted:
        return event
    else:
        return None


def search_events(**kwargs):
    query = db.session.query(Event)

    # filter out deleted events
    query = query.filter(Event.deleted is not True)

    if "query" in kwargs:
        query_string = kwargs.pop("query")
        query_text = ""
        for word in query_string.split():
            # this is to formulate a query string like 'twisted:* frequncey:*'
            if word == query_string.split()[-1]:
                query_text = query_text + (str(word) + str(":*"))
            else:
                query_text = query_text + (str(word) + str(":* & "))

        query = query.filter(
            Event.__ts_vector__.match(query_text, postgresql_regconfig="english")
        )

    return paginated_results(Event, query, **kwargs)


def add_event(**kwargs):
    creator = kwargs.pop("creator", None)
    name = kwargs.pop("name")
    description = kwargs.pop("description")
    location = kwargs.pop("location")
    dateTime = kwargs.pop("dateTime")
    rrule = kwargs.pop("rrule", None)
    url = kwargs.pop("url", None)
    tags = kwargs.pop("tags", None)
    images = kwargs.pop("images", None)

    event = Event(name=name, creator=creator, default_url=url, description=description)
    db.session.add(event)
    db.session.flush()

    if rrule:
        rrule = Rrule(
            event=event,
            recurring_type=rrule["recurringType"],
            separation_count=rrule["separationCount"],
            day_of_week=rrule["dayOfWeek"],
            week_of_month=rrule["weekOfMonth"],
            month_of_year=rrule["monthOfYear"],
            day_of_month=rrule["dayOfMonth"],
        )
        db.session.add(rrule)
        db.session.flush()

    if tags:
        event_tags.add_tags_to_event(tags, event)

    if images:
        # create new album and add images
        event_images.create_album_for_event(event, images, creator)

    # LOCATION
    event.default_location = event_locations.get_location(location["place_id"])
    if event.default_location is None:
        event.default_location = event_locations.add_new_event_location(
            creator, **location
        )

    # DATES
    event_dates.generate_future_event_dates(
        event, dateTime, event.default_location, rrule, url
    )

    db.session.commit()
    return event


def update_event(event_id, **kwargs):
    rrule = kwargs.get("rrule")
    url = kwargs.get("url")
    location = kwargs.get("location")
    dateTime = kwargs.get("dateTime")
    description = kwargs.get("description")
    tags = kwargs.get("tags")
    cover_album_id = kwargs.get("cover_album_id")

    print(kwargs)
    event = get_event_or_404(event_id)

    if url:
        event.default_url = url

    if description:
        event.description = description
        # activity = Activity(verb=u"update", object=event)
        # create_notification('UPDATE EVENT', activity, event.followers)
        # db.session.add(activity)

    if rrule is not None and rrule is False:
        db.session.delete(event.rrule)

    # require these three fields to update
    if dateTime and location and rrule:
        # delete existing rrule if exists
        if event.rrule:
            db.session.delete(event.rrule)
            db.session.flush()

        rrule = Rrule(
            event=event,
            recurring_type=rrule["recurringType"],
            separation_count=rrule["separationCount"],
            day_of_week=rrule["dayOfWeek"],
            week_of_month=rrule["weekOfMonth"],
            day_of_month=rrule["dayOfMonth"],
            month_of_year=rrule["monthOfYear"],
        )
        db.session.add(rrule)

        # location
        event_location = event_locations.get_location(location["place_id"])
        if event_location is None:
            event_location = event_locations.add_new_event_location(**location)
        event.default_location = event_location

        return event_dates.generate_future_event_dates(
            event, dateTime, event_location, rrule, url
        )

    if tags:
        event_tags.add_tags_to_event(tags, event)

    if cover_album_id:
        album = event_images.get_event_album_or_404(cover_album_id)
        event.cover_album = album

    db.session.commit()

    return event


def delete_event(event_id):
    event = get_event_or_404(event_id)
    event.deleted = True
    db.session.commit()
