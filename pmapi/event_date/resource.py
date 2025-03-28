import json
from flask import Blueprint

from marshmallow import fields
from flask_apispec import doc
from flask_apispec import marshal_with
from flask_apispec import MethodResource
from flask_apispec import use_kwargs
from flask_login import login_required
from flask_login import current_user
from pmapi.event.controllers import get_event_or_404
from pmapi.hcaptcha.controllers import validate_hcaptcha
from pmapi.suggestions.controllers import add_suggested_edit
from .schemas import EventDateSchema, EventDateListSchema, EventDateQueryListSchema
from pmapi.event.schemas import EventSchema

from . import permissions as event_date_permissions
import pmapi.event_date.controllers as event_dates
from pmapi.common.controllers import paginated_view_args
from pmapi.extensions import db

per_page = 20

event_dates_blueprint = Blueprint("dates", __name__)


@doc(tags=["dates"])
class DatesResource(MethodResource):
    @doc(
        summary="Get a list of event dates that are in the db.",
        description="""Returns a list of event dates that are in the db. \n
        ### Usage:  \n
        Start and end date format must be in ISO-8601 format.
        eg: 2020-05-23T05:00:00",
        """,
    )
    @use_kwargs(
        {
            "query": fields.Str(),
            "date_min": fields.DateTime(required=False),
            "date_max": fields.DateTime(required=False),
            "tags": fields.List(fields.Str(), required=False),
            "artists": fields.List(fields.Str(), required=False),
            "location": fields.Str(),
            "bounds": fields.Str(),
            "radius": fields.Int(),
            "duration_options": fields.List(fields.Integer(), required=False),
            "size_options": fields.List(fields.String(), required=False),
            "country_id": fields.Str(),
            "region_name": fields.Str(),
            "locality_id": fields.Str(),
            "favorites": fields.Boolean(),
            "sort_option": fields.Str(),
            "distinct": fields.Boolean(),
            "creator_user": fields.Str(),
            "host_user": fields.Str(),
            "interested_user": fields.Str(),
            "going_user": fields.Str(),
            "reviewed_user": fields.Str(),
            "following_user": fields.Str(),
            "all_related_to_user": fields.Str(),
            "empty_lineup": fields.Boolean(),
            "date_unconfirmed": fields.Boolean(),
            **paginated_view_args(sort_options=["created_at", "distance", "start"]),
        },
        location="query"
    )
    @marshal_with(EventDateQueryListSchema(), code=200)
    def get(self, **kwargs):
        # get json from query string
        print(kwargs)
        if kwargs.get("location"):
            kwargs["location"] = json.loads(kwargs["location"])
            print(kwargs['location'])

        if kwargs.get("bounds"):
            kwargs["bounds"] = json.loads(kwargs["bounds"])
        return event_dates.query_event_dates(**kwargs)


event_dates_blueprint.add_url_rule(
    "/", view_func=DatesResource.as_view("DatesResource")
)


@doc(tags=["dates"])
class DateResource(MethodResource):
    @doc(
        summary="Get an event date.",
        description="""Returns an event date \n
        """,
        params={"id": {"description": "event date ID"}},
    )
    @marshal_with(EventDateSchema(), code=200)
    def get(self, id):
        return event_dates.get_event_date_or_404(id)

    @doc(
        summary="Delete an event date.",
        description="""Delete an event date. Must be event creator or admin.""",
        params={"id": {"description": "event date ID"}},
    )
    @marshal_with(EventSchema(), code=200)
    @login_required
    @event_date_permissions.delete
    def delete(self, id):
        return event_dates.delete_event_date(id)

    @doc(
        summary="Update an event date.",
        description="""Update an event date. Must be event creator or admin.""",
        params={"id": {"description": "event date ID"}},
    )
    @use_kwargs(
        {
            "media_items": fields.List(fields.Dict(), required=False, allow_none=True),
            "lineup_images": fields.List(fields.Dict(), required=False, allow_none=True),
            "description": fields.Str(),
            "description_attribute": fields.Str(required=False, allow_none=True),
            "url": fields.Str(),
            "tickets": fields.List(fields.Dict(), required=False, allow_none=True),
            "ticket_url": fields.Str(required=False, allow_none=True),
            "size": fields.Integer(),
            "date_time": fields.Dict(),
            "location": fields.Dict(),
            "cancelled": fields.Boolean(),
            "add_artists": fields.List(fields.Dict(), required=False, allow_none=True),
            "remove_artists": fields.List(
                fields.Dict(), required=False, allow_none=True
            ),
            "update_artists": fields.List(
                fields.Dict(), required=False, allow_none=True
            ),
        }
    )
    @marshal_with(EventDateSchema(), code=200)
    @login_required
    @event_date_permissions.update
    def put(self, id, **kwargs):
        return event_dates.update_event_date(id, **kwargs)


event_dates_blueprint.add_url_rule(
    "/<id>", view_func=DateResource.as_view("DateResource")
)


@doc(tags=["dates", "user"])
class DateUserInterestedResource(MethodResource):
    @doc(
        summary="Mark as interested",
        description="""Add or remove this date from the users list of interested event dates""",
        params={"id": {"description": "event date ID"}},
    )
    @marshal_with(EventDateSchema(), code=200)
    @login_required
    def post(self, id, **kwargs):
        return event_dates.toggle_interested(id)


event_dates_blueprint.add_url_rule(
    "/<id>/interested", view_func=DateUserInterestedResource.as_view("DateUserInterestedResource")
)


@doc(tags=["dates", "user"])
class DateUserGoingResource(MethodResource):
    @doc(
        summary="Mark as going",
        description="""Add or remove this date from the users list of 'going' event dates""",
        params={"id": {"description": "event date ID"}},
    )
    @marshal_with(EventDateSchema(), code=200)
    @login_required
    def post(self, id, **kwargs):
        return event_dates.toggle_going(id)


event_dates_blueprint.add_url_rule(
    "/<id>/going", view_func=DateUserGoingResource.as_view("DateUserGoingResource")
)


@doc(tags=["dates"])
class DateIcsDownloadResource(MethodResource):
    @doc(
        summary="Get an ics file for this date",
        description="""Generates an ics (ical) format calendar file for this event date.""",
        params={"id": {"description": "event date ID"}},
    )
    def get(self, id, **kwargs):
        return event_dates.ics_download(id)


event_dates_blueprint.add_url_rule(
    "/<id>/ics", view_func=DateIcsDownloadResource.as_view("DateIcsDownloadResource")
)


@doc(tags=["dates"])
class EventDatesResource(MethodResource):
    @doc(
        summary="Add an event date to an existing event.",
        description="""Create an event date. Must be event creator or admin.""",
        params={"event_id": {"description": "event ID"}},
    )
    @login_required
    @event_date_permissions.add
    @use_kwargs(
        {
            "lineup_images": fields.List(fields.Dict(), required=False, allow_none=True),
            "description": fields.Str(required=False, allow_none=True),
            "description_attribute": fields.Str(required=False, allow_none=True),
            "url": fields.Str(required=False, allow_none=True),
            "ticket_url": fields.Str(required=False, allow_none=True),
            "size": fields.Integer(required=False, allow_none=True),
            "date_time": fields.Dict(required=True),
            "location": fields.Dict(required=True),
            "artists": fields.List(fields.Dict(), required=False, allow_none=True),
        }
    )
    @marshal_with(EventSchema(), code=200)
    def post(self, event_id, **kwargs):
        event = get_event_or_404(event_id)
        event = event_dates.add_event_date_with_datetime(event, **kwargs, creator=current_user)
        db.session.commit()
        return event

    @doc(
        summary="Get dates of an event.",
        description="""Get dates of an event.""",
        params={"id": {"description": "event date ID"}},
    )
    @marshal_with(EventDateSchema(many=True), code=200)
    def get(self, event_id):
        event = get_event_or_404(event_id)
        return event.event_dates

event_dates_blueprint.add_url_rule(
    "/event/<event_id>",
    view_func=EventDatesResource.as_view("EventDatesResource"),
)

"""
SUGGESTIONS
"""


@doc(tags=["dates"])
class EventDateSuggestAddResource(MethodResource):
    @doc(
        summary="Suggest adding an event date to an existing event.",
        params={"event_id": {"description": "event ID"}},
    )
    @use_kwargs(
        {
            "description": fields.Str(required=False, allow_none=True),
            "description_attribute": fields.Str(required=False, allow_none=True),
            "url": fields.Str(required=False, allow_none=True),
            "size": fields.Integer(required=False, allow_none=True),
            "date_time": fields.Dict(required=True),
            "location": fields.Dict(required=True),
            "artists": fields.List(fields.Dict(), required=False, allow_none=True),
            "message": fields.Str(required=False, allow_none=True),
            "hcaptcha_token": fields.Str(required=False, allow_none=True),
            "lineup_images": fields.List(fields.Dict(), required=False, allow_none=True),
            
        }
    )
    @marshal_with(EventDateSchema(), code=200)
    def post(self, event_id, **kwargs):
        event = get_event_or_404(event_id)
        # used by unpriviliged users to suggest updates to an event
        token = kwargs.pop("hcaptcha_token", None)
        if not current_user.is_authenticated:
            validate_hcaptcha(token)

        return add_suggested_edit(
            event=event,
            action="create",
            object_type="EventDate",
            creator_id=current_user.get_id(),
            **kwargs
        )

event_dates_blueprint.add_url_rule(
    "/event/<event_id>/suggest",
    view_func=EventDateSuggestAddResource.as_view(
        "EventDateSuggestAddResource"),
)


@doc(tags=["dates", "suggest_edit"])
class EventDateSuggestResource(MethodResource):
    @doc(
        summary="Suggest deleting an event date.",
        params={"id": {"description": "event date ID"}},
    )
    @use_kwargs(
        {
            "message": fields.Str(required=False, allow_none=True),
            "hcaptcha_token": fields.Str(required=False, allow_none=True),
        }
    )
    def delete(self, id, **kwargs):
        # used by unpriviliged users to suggest updates to an event
        token = kwargs.pop("hcaptcha_token", None)
        event_date = event_dates.get_event_date_or_404(id)
        if not current_user.is_authenticated:
            validate_hcaptcha(token)
                
        return add_suggested_edit(
            event=event_date.event,
            event_date=event_date,
            creator_id=current_user.get_id(),
            action="delete",
            object_type="EventDate",
            **kwargs
        )
    
    @doc(summary="Suggest an edit to an event date")
    @use_kwargs(
        {
            "description": fields.Str(),
            "description_attribute": fields.Str(required=False, allow_none=True),
            "url": fields.Str(),
            "size": fields.Integer(),
            "date_time": fields.Dict(),
            "location": fields.Dict(),
            "cancelled": fields.Boolean(),
            "lineup_images": fields.List(fields.Dict(), required=False, allow_none=True),
            "add_artists": fields.List(fields.Dict(), required=False, allow_none=True),
            "remove_artists": fields.List(
                fields.Dict(), required=False, allow_none=True
            ),
            "update_artists": fields.List(
                fields.Dict(), required=False, allow_none=True
            ),
            "message": fields.Str(required=False, allow_none=True),
            "hcaptcha_token": fields.Str(required=False, allow_none=True),
        }
    )
    def put(self, id, **kwargs):
        # used by unpriviliged users to suggest updates to an event
        token = kwargs.pop("hcaptcha_token", None)
        event_date = event_dates.get_event_date_or_404(id)
        if not current_user.is_authenticated:
            validate_hcaptcha(token)

        return add_suggested_edit(
            event=event_date.event,
            event_date=event_date,
            creator_id=current_user.get_id(),
            action="update",
            object_type="EventDate",
            **kwargs
        )


event_dates_blueprint.add_url_rule(
    "/<id>/suggest",
    view_func=EventDateSuggestResource.as_view("EventDateSuggestResource"),
)
