import json
from flask import Blueprint

from marshmallow import fields
from flask_apispec import doc
from flask_apispec import marshal_with
from flask_apispec import MethodResource
from flask_apispec import use_kwargs
from flask_login import login_required
from flask_login import current_user
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
            "region_id": fields.Str(),
            "locality_id": fields.Str(),
            "favorites": fields.Boolean(),
            "sort_option": fields.Str(),
            "distinct": fields.Boolean(),
            **paginated_view_args(sort_options=["created_at"]),
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
            "description": fields.Str(),
            "description_attribute": fields.Str(required=False, allow_none=True),
            "url": fields.Str(),
            "ticket_url": fields.Str(),
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
            "description_attribute": fields.Str(required=False, allow_none=True),
            "url": fields.Str(required=False, allow_none=True),
            "ticket_url": fields.Str(required=False, allow_none=True),
            "size": fields.Integer(required=False, allow_none=True),
            "date_time": fields.Dict(required=True),
            "location": fields.Dict(required=True),
            "artists": fields.List(fields.Dict(), required=False, allow_none=True),
        }
    )
    @marshal_with(EventDateSchema(), code=200)
    def post(self, event_id, **kwargs):
        event_date = event_dates.add_event_date_with_datetime(
            event_id, **kwargs, creator=current_user
        )
        db.session.commit()
        return event_date

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
        }
    )
    @marshal_with(EventDateSchema(), code=200)
    def post(self, event_id, **kwargs):
        event_dates.suggest_add(event_id, **kwargs)


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
        print(kwargs)
        event_dates.suggest_delete(id, **kwargs)
        return "", 204

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
        event_dates.suggest_update(id, **kwargs)
        return "", 200


event_dates_blueprint.add_url_rule(
    "/<id>/suggest",
    view_func=EventDateSuggestResource.as_view("EventDateSuggestResource"),
)
