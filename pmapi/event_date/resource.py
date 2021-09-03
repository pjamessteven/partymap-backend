import json
from flask import Blueprint

from marshmallow import fields
from flask_apispec import doc
from flask_apispec import marshal_with
from flask_apispec import MethodResource
from flask_apispec import use_kwargs
from flask_login import login_required
from flask_login import current_user
from .schemas import EventDateSchema, EventDateListSchema
from . import permissions as event_date_permissions
import pmapi.event_date.controllers as event_dates
from pmapi.common.controllers import paginated_view_args

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
            "date_min": fields.DateTime(required=False),
            "date_max": fields.DateTime(required=False),
            "tags": fields.List(fields.Str(), required=False),
            "location": fields.Str(),
            "bounds": fields.Str(),
            "distinct_event": fields.Boolean(),
            "duration_options": fields.List(fields.Integer(), required=False),
            "size_options": fields.List(fields.String(), required=False),
            **paginated_view_args(sort_options=["created_at"]),
        },
        location="query",
    )
    @marshal_with(EventDateListSchema(), code=200)
    def get(self, **kwargs):
        # get json from query string
        if kwargs.get("location"):
            print(kwargs.get("location"))
            kwargs["location"] = json.loads(kwargs["location"])
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
    @login_required
    @event_date_permissions.delete
    def delete(self, id):
        event_dates.delete_event_date(id)
        return "", 204

    @doc(
        summary="Update an event date.",
        description="""Update an event date. Must be event creator or admin.""",
        params={"id": {"description": "event date ID"}},
    )
    @use_kwargs(
        {
            "description": fields.Str(),
            "url": fields.Str(),
            "ticketUrl": fields.Str(),
            "size": fields.Integer(),
            "dateTime": fields.Dict(),
            "location": fields.Dict(),
            "cancelled": fields.Boolean(),
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
            "description": fields.Str(required=False, allow_none=True),
            "url": fields.Str(required=False, allow_none=True),
            "ticketUrl": fields.Str(required=False, allow_none=True),
            "size": fields.Integer(required=False, allow_none=True),
            "dateTime": fields.Dict(required=True),
            "location": fields.Dict(required=True),
        }
    )
    @marshal_with(EventDateSchema(), code=200)
    def post(self, event_id, **kwargs):
        return event_dates.add_event_date_with_datetime(
            event_id, **kwargs, creator=current_user
        )

    @doc(
        summary="Get dates of an event.",
        description="""Get dates of an event.""",
        params={"id": {"description": "event date ID"}},
    )
    @marshal_with(EventDateSchema(many=True), code=200)
    def get(self, event_id):
        return event_dates.get_event_dates_for_event(event_id)


event_dates_blueprint.add_url_rule(
    "/event/<event_id>",
    view_func=EventDatesResource.as_view("EventDatesResource"),
)
