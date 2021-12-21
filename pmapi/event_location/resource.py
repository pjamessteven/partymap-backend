from flask import Blueprint

from marshmallow import fields
from flask_apispec import doc
from flask_apispec import marshal_with
from flask_apispec import MethodResource
from flask_apispec import use_kwargs

from pmapi.common.controllers import paginated_view_args
import pmapi.event_location.controllers as event_locations
from .schemas import PointSchema, LocationSchema, LocationListSchema, CountrySchema


locations_blueprint = Blueprint("locations", __name__)


@doc(tags=["locations"])
class LocationsResource(MethodResource):
    @doc(
        summary="Get a list of locations that are in the db.",
        description="""Returns a list of locations that are in the db. \n
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
            **paginated_view_args(sort_options=["created_at"]),
        },
        location="query",
    )
    @marshal_with(LocationListSchema(), code=200)
    def get(self, **kwargs):
        return event_locations.get_all_locations_paginated(**kwargs)


locations_blueprint.add_url_rule(
    "/", view_func=LocationsResource.as_view("LocationsResource")
)


@doc(tags=["locations"])
class LocationResource(MethodResource):
    @doc(
        summary="Get location information, including upcoming events.",
        description="Returns information about a specific place_id.",
        params={"place_id": {"description": "place_id of location"}},
    )
    @marshal_with(LocationSchema(), code=200)
    def get(self, place_id):
        return event_locations.get_location_or_404(place_id)


locations_blueprint.add_url_rule(
    "/<place_id>", view_func=LocationResource.as_view("LocationResource")
)


@doc(tags=["locations"])
class PointsResource(MethodResource):
    @doc(
        summary="Get all event location points",
        description="""Returns the latitude and longitude of all unique event \
        within a specified time period. Also supports filtering by tag. \
        This resource is used to show the points on the map.
        ### Usage:
        Start and end date format must be in ISO-8601 format.
        eg: 2020-05-23T05:00:00",
        """,
    )
    @use_kwargs(
        {
            "date_min": fields.DateTime(required=False),
            "date_max": fields.DateTime(required=False),
            "tags": fields.List(fields.Str(), required=False),
            "artists": fields.List(fields.Int(), required=False),
            "favorites": fields.Boolean(),
            "duration_options": fields.List(fields.Integer(), required=False),
            "size_options": fields.List(fields.String(), required=False),
            "query": fields.Str(),
        },
        location="query",
    )
    @marshal_with(PointSchema(many=True), code=200)
    def get(self, **kwargs):
        return event_locations.get_all_locations(**kwargs)


locations_blueprint.add_url_rule(
    "/points/", view_func=PointsResource.as_view("PointsResource")
)


@doc(tags=["locations"])
class LocalitiesResource(MethodResource):
    @doc(
        summary="Get all localities",
        description="""Returns an object containing all localities in the db. \n
        ### Usage:  \n

        """,
    )
    @marshal_with(CountrySchema(many=True), code=200)
    def get(self, **kwargs):
        return event_locations.get_all_countries()


locations_blueprint.add_url_rule(
    "/localities", view_func=LocalitiesResource.as_view("LocalitiesResource")
)
