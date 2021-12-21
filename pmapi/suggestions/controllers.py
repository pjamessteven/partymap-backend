from .model import SuggestedEdit


from pmapi import exceptions as exc
from pmapi.extensions import db, activity_plugin
from datetime import datetime
from flask_login import current_user, login_user
from sqlalchemy_continuum import version_class, transaction_class
from sqlalchemy import cast, or_, and_, func, select, join
from sqlalchemy.orm import with_expression
from pmapi.event_date.model import EventDate
from pmapi.user.model import User
import pmapi.user.controllers as users
import pmapi.event_tag.controllers as event_tags
import pmapi.media_item.controllers as media_items
import pmapi.event_date.controllers as event_dates
import pmapi.event.controllers as events
import pmapi.user.controllers as users
import pmapi.event_location.controllers as event_locations
from pmapi.common.controllers import paginated_results
from sqlalchemy import inspect
import pprint

Activity = activity_plugin.activity_cls


def get_suggested_edit_or_404(id):
    item = get_suggested_edit(id)
    if not item:
        msg = "No such edit with id {}".format(id)
        raise exc.RecordNotFound(msg)
    return item


def get_suggested_edit(id):
    item = SuggestedEdit.query.get(id)
    if item:
        return item
    else:
        return None


def get_suggested_edits(**kwargs):
    query = db.session.query(SuggestedEdit)

    if "event_id" in kwargs:
        query = query.filter(SuggestedEdit.event_id == kwargs.pop("event_id"))

    if "status" in kwargs:
        query = query.filter(SuggestedEdit.status == kwargs.pop("status"))

    return paginated_results(SuggestedEdit, query=query, **kwargs)


def add_suggested_edit(
    event_id, action, object_type=None, event_date_id=None, **kwargs
):
    print("ED ID", event_date_id)
    # check that event and event_date both exist
    events.get_event_or_404(event_id)
    if event_date_id:
        event_dates.get_event_date_or_404(event_date_id)

    message = kwargs.pop("message", None)

    creator_id = None
    if current_user.get_id():
        creator_id = current_user.get_id()

    suggested_edit = SuggestedEdit(
        event_id=event_id,
        event_date_id=event_date_id,
        action=action,
        object_type=object_type,
        kwargs=kwargs,
        message=message,
        creator_id=creator_id,  # MUST USE ID HERE BECAUSE ANON USER
    )

    db.session.add(suggested_edit)
    db.session.commit()
    return


def update_suggested_edit(id, **kwargs):
    print("update", kwargs)
    suggestion = get_suggested_edit_or_404(id)
    event = events.get_event_or_404(suggestion.event_id)

    status = kwargs.pop("status", None)
    # log out then log back in so the transaction_id is that of the suggester
    requesting_user = users.get_user_or_404(current_user.id)

    if status == "approved":
        if suggestion.status == "approved":
            raise exc.InvalidAPIRequest("Suggestion has already been approved")

        if current_user.is_authenticated:
            suggestion.approved_by = requesting_user

        # login as user who created suggestion
        if suggestion.creator is not None:
            login_user(suggestion.creator, force=True)

        # process request
        if suggestion.action == "create":
            if suggestion.object_type == "EventDate":
                # create event date
                event_dates.add_event_date_with_datetime(event, **suggestion.kwargs)

        if suggestion.action == "update":
            if suggestion.object_type == "EventDate":
                # update event date
                event_dates.update_event_date(
                    suggestion.event_date_id, **suggestion.kwargs
                )

            elif suggestion.object_type == "Event":
                events.update_event(
                    suggestion.event_id, is_suggestion=True, **suggestion.kwargs
                )

        if suggestion.action == "delete":
            if suggestion.object_type == "EventDate":
                # create event date
                event_dates.delete_event_date(suggestion.event_date_id)

        suggestion.status = "approved"
        suggestion.approved_at = datetime.utcnow()

    if status == "hidden":
        if suggestion.status == "approved":
            raise exc.InvalidAPIRequest("Suggestion has already been approved")
        suggestion.status = "hidden"

    if status == "pending":
        if suggestion.status == "approved":
            raise exc.InvalidAPIRequest("Suggestion has already been approved")
        suggestion.status = "pending"

    db.session.commit()

    # log back in as original user
    if suggestion.creator is not None:
        login_user(requesting_user, remember=True)

    return suggestion


def delete_suggested_edit(**kwargs):
    edit = get_suggested_edit_or_404(id)
    db.session.delete(edit)
    db.session.commit()
