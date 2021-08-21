from .model import Event, Rrule
from pmapi import exceptions as exc
from pmapi.extensions import db
from datetime import datetime
from flask_login import current_user

import pmapi.event_tag.controllers as event_tags
import pmapi.media_item.controllers as media_items
import pmapi.event_date.controllers as event_dates
import pmapi.event_location.controllers as event_locations
from pmapi.common.controllers import paginated_results


def get_event_or_404(id):
    event = get_event(id)
    if not event:
        msg = "No such event with id {}".format(id)
        raise exc.RecordNotFound(msg)
    return event


def get_event(id):
    event = Event.query.get(str(id))  # uuid to string
    if event:
        return event
    else:
        return None


def search_events(**kwargs):
    query = db.session.query(Event)

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
    media = kwargs.pop("media_items", None)

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

    if media:
        media_items.add_media_to_event(media, event, creator=creator)

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
    print(kwargs)

    rrule = kwargs.get("rrule")
    remove_rrule = kwargs.get("remove_rrule")
    url = kwargs.get("url")
    location = kwargs.get("location")
    dateTime = kwargs.get("dateTime")
    description = kwargs.get("description")
    tags = kwargs.get("tags")
    media = kwargs.pop("media_items", None)

    event = get_event_or_404(event_id)
    event.updated_at = datetime.utcnow()

    if url:
        event.default_url = url

    if description:
        event.description = description
        # activity = Activity(verb=u"update", object=event)
        # create_notification('UPDATE EVENT', activity, event.followers)
        # db.session.add(activity)

    if remove_rrule is True:
        print("remove rrule")
        if event.rrule:
            db.session.delete(event.rrule)
            # delete future event dates (not including the next one)
            for ed in event.future_event_dates_except_next:
                db.session.delete(ed)

    # require these three fields to update
    if dateTime and location and rrule:
        # delete existing rrule if exists
        existing_rrule = Rrule.query.get(event_id)
        if existing_rrule:
            db.session.delete(existing_rrule)
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
        db.session.flush()

        # location
        print("place_i", location["place_id"])
        event_location = event_locations.get_location(location["place_id"])
        print(event_location)
        if event_location is None:
            print("el is none")
            event_location = event_locations.add_new_event_location(**location)
            print(event_location)
        event.default_location = event_location

        return event_dates.generate_future_event_dates(
            event, dateTime, event_location, rrule, url
        )

    if tags:
        event_tags.add_tags_to_event(tags, event)

    if media:
        media_items.add_media_to_event(media, event, creator=current_user)

    db.session.commit()

    return event


def delete_event(event_id):
    event = get_event_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
