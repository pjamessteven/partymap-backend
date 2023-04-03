from .model import Event, Rrule, user_event_following_table, event_page_views_table
from pmapi import exceptions as exc
from pmapi.extensions import db, Session, activity_plugin
from datetime import datetime
from flask_login import current_user
from sqlalchemy_continuum import version_class, transaction_class
from sqlalchemy import cast, or_, and_, func, select, join
from sqlalchemy.orm import with_expression
from pmapi.event_date.model import EventDate, user_event_date_going_table, user_event_date_interested_table
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
from flask_login import current_user, login_user
from pmapi.config import BaseConfig
from sqlalchemy_continuum import versioning_manager
import pprint
from pmapi.mail.controllers import (
    send_new_event_notification,
)

Activity = activity_plugin.activity_cls


def get_event_or_404(id):
    event = get_event(id)
    if not event:
        msg = "No such event with id {}".format(id)
        raise exc.RecordNotFound(msg)
    return event


def get_event(id):
    following_expression = (
        db.session.query(user_event_following_table)
        .filter(
            and_(
                user_event_following_table.c.user_id == current_user.id,
                user_event_following_table.c.event_id == id,
            )
        )
        .exists()
    )

    event = (
        db.session.query(Event)
        .filter(Event.id == id)
        .options(
            with_expression(
                Event.user_following,
                following_expression,
            )
        )
    ).first()

    if event:
        # increment page views
        user_id = None
        if current_user.is_authenticated:
            user_id = current_user.id
        event.increment_page_views(user_id)
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
            Event.__ts_vector__.match(
                query_text, postgresql_regconfig="english")
        )

    if "created_by" in kwargs:
        user = users.get_user_or_404(kwargs.pop("created_by"))
        query = query.filter(Event.creator_id == user.id)

    if "hidden" in kwargs:
        query = query.filter(Event.hidden == True)

    return paginated_results(Event, query=query, **kwargs)


def add_event(**kwargs):
    creator = kwargs.pop("creator", None)
    host = kwargs.pop("host", False)
    name = kwargs.pop("name")
    description = kwargs.pop("description")
    description_attribute = kwargs.pop("description_attribute", None)
    next_event_date_description = kwargs.pop("next_event_date_description")
    next_event_date_description_attribute = kwargs.pop(
        "next_event_date_description_attribute"
    )
    next_event_date_size = kwargs.pop("next_event_date_size")
    next_event_date_artists = kwargs.pop("next_event_date_artists", None)
    location = kwargs.pop("location")
    date_time = kwargs.pop("date_time")
    rrule = kwargs.pop("rrule", None)
    url = kwargs.pop("url", None)
    ticket_url = kwargs.pop("ticket_url", None)
    tags = kwargs.pop("tags", None)
    media = kwargs.pop("media_items", None)

    # Check if location already exists
    loc = event_locations.get_location(location["place_id"])
    if loc is None:
        # create location if not
        loc = event_locations.add_new_event_location(creator, **location)

    event = Event(
        name=name,
        creator_id=creator.id,
        host_id=creator.id if host is True else None,
        description=description,
        description_attribute=description_attribute,
    )
    db.session.add(event)
    db.session.flush()

    # separation count of 0 means no recurrance
    if rrule and rrule["separationCount"] > 0:
        rrule = Rrule(
            recurring_type=rrule["recurringType"],
            separation_count=rrule["separationCount"],
            day_of_week=rrule["dayOfWeek"],
            week_of_month=rrule["weekOfMonth"],
            month_of_year=rrule["monthOfYear"],
            day_of_month=rrule["dayOfMonth"],
            start_date_time=date_time["start"],
            end_date_time=date_time["end"],
            default_url=url,
            default_ticket_url=ticket_url,
            default_location=loc,
        )
        db.session.add(rrule)
        db.session.flush()
        event.rrule = rrule
    else:
        rrule = None

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
        date_time,
        loc,
        rrule,
        url,
        ticket_url,
        next_event_date_description,
        next_event_date_description_attribute,
        next_event_date_size,
        next_event_date_artists,
    )

    db.session.commit()

    # send notification
    """
    send_new_event_notification(
        event, creator.username if creator is not None else None
    )
    """
    return event


def suggest_delete(event_id, **kwargs):
    token = kwargs.pop("hcaptcha_token", None)
    get_event_or_404(event_id)
    if not current_user.is_authenticated:
        if not validate_hcaptcha(token):
            raise InvalidAPIRequest("HCaptcha not valid")
    return suggestions.add_suggested_edit(
        event_id=event_id, action="delete", object_type="Event", **kwargs
    )


def suggest_update(event_id, **kwargs):
    # used by unpriviliged users to suggest updates to an event
    token = kwargs.pop("hcaptcha_token", None)
    get_event_or_404(event_id)
    if not current_user.is_authenticated:
        if not validate_hcaptcha(token):
            raise InvalidAPIRequest("HCaptcha not valid")
    return suggestions.add_suggested_edit(
        event_id=event_id,
        action="update",
        creator_id=current_user.get_id(),
        object_type="Event",
        event_date_id=None,
        **kwargs
    )


def update_event(event_id, **kwargs):
    rrule = kwargs.get("rrule")
    remove_rrule = kwargs.get("remove_rrule")
    url = kwargs.get("url")
    location = kwargs.get("location")
    date_time = kwargs.get("date_time")
    description = kwargs.get("description")
    description_attribute = kwargs.get("description_attribute", None)
    name = kwargs.get("name")
    add_tags = kwargs.get("add_tags", None)
    remove_tags = kwargs.get("remove_tags", None)
    media = kwargs.pop("media_items", None)
    is_suggestion = kwargs.get("is_suggestion", False)
    hidden = kwargs.get("hidden", None)

    event = get_event_or_404(event_id)
    existing_rrule = db.session.query(Rrule).filter(
        Rrule.id == event.rrule_id).first()

    # this field is useful for triggering
    # a new version of this object in continuum
    event.updated_at = datetime.utcnow()

    if hidden is not None:
        event.hidden = hidden

    if name or description or description_attribute is not None:
        if name:
            event.name = name

        if description:
            event.description = description

        if description_attribute is not None:
            event.description_attribute = description_attribute

        # add activity
        db.session.flush()
        activity = Activity(verb=u"update", object=event, target=event)
        db.session.add(activity)

    if remove_rrule is True:
        if existing_rrule is not None:
            db.session.delete(existing_rrule)
            db.session.flush()
            # add activity for delete rrule activity
            activity = Activity(
                verb=u"delete", object=existing_rrule, target=event)
            db.session.add(activity)

    if add_tags is not None and len(add_tags) > 0:
        event_tags.add_tags_to_event(
            add_tags, event
        )  # will remove tag if it already exists

    if remove_tags is not None and len(remove_tags) > 0:
        event_tags.add_tags_to_event(
            remove_tags, event
        )  # will remove tag if it already exists

    if media:
        if is_suggestion:
            # delete previous media
            # as community events can only have one image
            media_items.remove_all_media_from_event(event)

        media_items.add_media_to_event(media, event, creator=current_user)

    # require these three fields to update
    # separtion count of 0 means no recurrance
    if date_time and location and rrule and rrule["separationCount"] > 0:

        # location
        event_location = event_locations.get_location(location["place_id"])
        if event_location is None:
            event_location = event_locations.add_new_event_location(**location)

        # delete existing rrule if exists
        if existing_rrule is not None:
            existing_rrule.recurring_type = rrule["recurringType"]
            existing_rrule.separation_count = rrule["separationCount"]
            existing_rrule.day_of_week = rrule["dayOfWeek"]
            existing_rrule.month_of_year = rrule["monthOfYear"]
            existing_rrule.week_of_month = rrule["weekOfMonth"]
            existing_rrule.start_date_time = date_time["start"]
            existing_rrule.end_date_time = date_time["end"]
            existing_rrule.default_url = url
            existing_rrule.default_location = event_location
            db.session.flush()
            activity = Activity(
                verb=u"update", object=existing_rrule, target=event)
            db.session.add(activity)
            rrule = existing_rrule

        else:
            rrule = Rrule(
                recurring_type=rrule["recurringType"],
                separation_count=rrule["separationCount"],
                day_of_week=rrule["dayOfWeek"],
                week_of_month=rrule["weekOfMonth"],
                day_of_month=rrule["dayOfMonth"],
                month_of_year=rrule["monthOfYear"],
                start_date_time=date_time["start"],
                end_date_time=date_time["end"],
                default_url=url,
                default_location=event_location,
            )
            db.session.add(rrule)
            # activity for creating rrule
            db.session.flush()
            event.rrule = rrule
            activity = Activity(verb=u"create", object=rrule, target=event)
            db.session.add(activity)

        # session.flush()
        # db.session.commit()

    # db.session.commit()

    if (date_time and location and rrule) or remove_rrule:
        # perform event_date add/delete as system user
        # manually create new transaction
        # requesting_user_id = current_user.id
        # db.session.expunge_all()  # start new session for bot user

        # requesting_user = users.get_user_or_404(requesting_user_id)
        # bot = users.get_user_or_404(BaseConfig.SYSTEM_USER_ID)
        # login_user(bot, force=True)

        # event = get_event_or_404(event_id)
        # event.updated_at = datetime.utcnow()

        if remove_rrule:
            # delete future event dates (not including the next one)
            # login as bot user for following action
            event_dates.delete_future_event_dates(
                event, preserve_next=True, activity=False
            )

        if date_time and location and rrule:
            event_dates.delete_future_event_dates(
                event, preserve_next=False, activity=False
            )
            print(rrule.week_of_month)
            event_dates.generate_future_event_dates(
                event, date_time, rrule.default_location, rrule, activity=False
            )

    db.session.commit()
    # login_user(requesting_user, force=True, remember=True)

    return event


def delete_event(event_id):
    event = get_event_or_404(event_id)

    # delete shit
    for event_tag in event.event_tags:
        db.session.delete(event_tag)
    for event_date in event.event_dates:
        for artist in event_date.artists:
            db.session.delete(artist)
        for suggestion in event_date.suggestions:
            db.session.delete(suggestion)
        db.session.delete(event_date)
    for media_item in event.media_items:
        db.session.delete(media_item)
    for suggestion in event.suggestions:
        db.session.delete(suggestion)
    for report in event.reports:
        db.session.delete(report)
    if event.rrule:
        db.session.delete(event.rrule)

    # delete page views
    db.engine.execute(
        event_page_views_table.delete(
            event_page_views_table.c.event_id == event_id)
    )

    db.session.commit()
    db.session.delete(event)

    # add activity
    db.session.flush()
    activity = Activity(verb=u"delete", object=event, target=event)
    db.session.add(activity)

    db.session.commit()


def favorite_event(event_id, **kwargs):
    event = get_event_or_404(event_id)
    user = current_user

    if event not in user.favorite_events:
        user.favorite_events.append(event)
    else:
        user.favorite_events.remove(event)

    db.session.commit()
    return event
