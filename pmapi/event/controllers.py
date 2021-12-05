from .model import Event, Rrule
from pmapi import exceptions as exc
from pmapi.extensions import db, activity_plugin
from datetime import datetime
from flask_login import current_user
from sqlalchemy_continuum import version_class, transaction_class
from sqlalchemy import cast, or_, and_, func, select, join
from sqlalchemy.orm import with_expression
from pmapi.event_date.model import EventDate
from pmapi.user.model import User
import pmapi.user.controllers as users
import pmapi.event_tag.controllers as event_tags
import pmapi.media_item.controllers as media_items
import pmapi.event_date.controllers as event_dates
import pmapi.event_location.controllers as event_locations
import pmapi.suggestions.controllers as suggestions
from pmapi.common.controllers import paginated_results
from pmapi.hcaptcha.controllers import validate_hcaptcha
from pmapi.exceptions import InvalidAPIRequest

import pprint

Activity = activity_plugin.activity_cls


def get_event_or_404(id):
    event = get_event(id)
    if not event:
        msg = "No such event with id {}".format(id)
        raise exc.RecordNotFound(msg)
    return event


def get_event(id):
    event = Event.query.get(id)
    if event:
        return event
    else:
        return None


def get_event_versions(event_id, **kwargs):
    EventVersion = version_class(Event)

    query = (
        db.session.query(EventVersion)
        .filter(EventVersion.id == event_id)
        .order_by(EventVersion.transaction_id.desc())
    )

    return paginated_results(EventVersion, query=query, **kwargs)


def get_event_contributors(event_id, **kwargs):
    EventVersion = version_class(Event)
    EventTransaction = transaction_class(Event)

    query = (
        db.session.query(User, func.count(EventTransaction.id))
        .join(EventTransaction, User.id == EventTransaction.user_id)
        .join(EventVersion, EventTransaction.id == EventVersion.transaction_id)
        .filter(EventVersion.id == event_id)
        .group_by(User.id)
    )
    return paginated_results(User, query=query, **kwargs)


def search_events(**kwargs):
    query = db.session.query(Event)
    print(kwargs)
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

    if "created_by" in kwargs:
        user = users.get_user_or_404(kwargs.pop("created_by"))
        query = query.filter(Event.creator_id == user.id)

    return paginated_results(Event, query=query, **kwargs)


def add_event(**kwargs):
    creator = kwargs.pop("creator", None)
    name = kwargs.pop("name")
    description = kwargs.pop("description")
    next_event_date_description = kwargs.pop("next_event_date_description")
    next_event_date_size = kwargs.pop("next_event_date_size")
    location = kwargs.pop("location")
    dateTime = kwargs.pop("dateTime")
    rrule = kwargs.pop("rrule", None)
    url = kwargs.pop("url", None)
    ticket_url = kwargs.pop("ticket_url", None)
    tags = kwargs.pop("tags", None)
    media = kwargs.pop("media_items", None)
    next_event_date_artists = kwargs.pop("next_event_date_artists", None)

    # Check if location already exists
    loc = event_locations.get_location(location["place_id"])
    if loc is None:
        # create location if not
        loc = event_locations.add_new_event_location(creator, **location)

    event = Event(
        name=name,
        creator=creator,
        default_url=url,
        default_ticket_url=ticket_url,
        default_location=loc,
        description=description,
    )
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

    # add activity
    activity = Activity(verb=u"create", object=event, target=event)
    db.session.add(activity)

    # DATES
    event_dates.generate_future_event_dates(
        event,
        dateTime,
        loc,
        rrule,
        url,
        ticket_url,
        next_event_date_description,
        next_event_date_size,
        next_event_date_artists,
    )

    db.session.commit()
    return event


1


def suggest_delete(event_id, **kwargs):
    token = kwargs.pop("hcaptcha_token")
    if validate_hcaptcha(token):
        # used by unpriviliged users to suggest updates to an event
        get_event_or_404(event_id)
        return suggestions.add_suggested_edit(
            event_id=event_id, action="delete", object_type="Event", **kwargs
        )
    else:
        raise InvalidAPIRequest("HCaptcha not valid")


def suggest_update(event_id, **kwargs):
    # used by unpriviliged users to suggest updates to an event
    token = kwargs.pop("hcaptcha_token")
    if validate_hcaptcha(token):
        get_event_or_404(event_id)
        return suggestions.add_suggested_edit(
            event_id=event_id, action="update", object_type="Event", **kwargs
        )
    else:
        raise InvalidAPIRequest("HCaptcha not valid")


def update_event(event_id, **kwargs):
    rrule = kwargs.get("rrule")
    remove_rrule = kwargs.get("remove_rrule")
    url = kwargs.get("url")
    location = kwargs.get("location")
    dateTime = kwargs.get("dateTime")
    description = kwargs.get("description")
    name = kwargs.get("name")
    add_tags = kwargs.get("add_tags")
    remove_tags = kwargs.get("remove_tags")
    media = kwargs.pop("media_items", None)
    is_suggestion = kwargs.get("is_suggestion", False)

    event = get_event_or_404(event_id)
    existing_rrule = Rrule.query.get(event_id)

    # this field is useful for triggering
    # a new version of this object in continuum

    event.updated_at = datetime.utcnow()

    if name:
        event.name = name
        # add activity
        db.session.flush()
        activity = Activity(verb=u"update", object=event, target=event)
        db.session.add(activity)

    if description:
        event.description = description
        # add activity
        db.session.flush()
        activity = Activity(verb=u"update", object=event, target=event)
        db.session.add(activity)

    if remove_rrule is True:
        if existing_rrule is not None:
            db.session.delete(existing_rrule)
            # delete future event dates (not including the next one)
            event_dates.delete_future_event_dates(event, preserve_next=True)
            # add activity
            db.session.flush()
            activity = Activity(verb=u"delete", object=existing_rrule, target=event)
            db.session.add(activity)

    # require these three fields to update
    if dateTime and location and rrule:
        # delete existing rrule if exists
        if existing_rrule is not None:
            db.session.delete(existing_rrule)
            # activity for deleting rrule
            db.session.flush()
            activity = Activity(verb=u"delete", object=existing_rrule, target=event)
            db.session.add(activity)
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
        # activity for creating rrule
        db.session.flush()
        activity = Activity(verb=u"create", object=rrule, target=event)
        db.session.add(activity)

        # location
        event_location = event_locations.get_location(location["place_id"])
        if event_location is None:
            event_location = event_locations.add_new_event_location(**location)
        event.default_location = event_location

        if url:
            event.default_url = url

        event_dates.delete_future_event_dates(event, preserve_next=False)

        event_dates.generate_future_event_dates(
            event, dateTime, event_location, rrule, url, None
        )

    if add_tags:
        event_tags.add_tags_to_event(
            add_tags, event
        )  # will remove tag if it already exists

    if remove_tags:
        event_tags.add_tags_to_event(
            remove_tags, event
        )  # will remove tag if it already exists

    if media:
        if is_suggestion:
            # delete previous media
            # as community events can only have one image
            media_items.remove_all_media_from_event(event)

        media_items.add_media_to_event(media, event, creator=current_user)

    db.session.commit()

    return event


def delete_event(event_id):
    event = get_event_or_404(event_id)

    # delete shit
    for event_tag in event.event_tags:
        db.session.delete(event_tag)
    for event_date in event.event_dates:
        db.session.delete(event_date)
    for media_item in event.media_items:
        db.session.delete(media_item)
    db.session.delete(event.rrule)

    db.session.commit()
    db.session.delete(event)

    # add activity
    db.session.flush()
    activity = Activity(verb=u"delete", object=event, target=event)
    db.session.add(activity)

    db.session.commit()
