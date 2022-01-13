from marshmallow import fields
from marshmallow import Schema

from pmapi.common.schemas import PaginatedSchema
from pmapi.event_date.schemas import EventDateSchema


class LocationSchema(Schema):
    geohash = fields.Str()
    lat = fields.Float()
    lng = fields.Float()
    name = fields.Str()
    description = fields.Str()
    locality = fields.Nested("LocalitySchema")
    country = fields.Str()
    city = fields.Str()
    address_components = fields.Str()
    place_id = fields.Str()
    event_dates = fields.Nested(EventDateSchema, many=True)


class LocationListSchema(PaginatedSchema):
    items = fields.Nested("LocationSchema", many=True)


class LocalitySchema(Schema):
    id = fields.Str()
    short_name = fields.Str()
    long_name = fields.Str()
    country = fields.Nested("CountrySchema", only=["short_name", "long_name"])
    region = fields.Nested("RegionSchema", only=["short_name", "long_name", "id"])


class RegionSchema(Schema):
    id = fields.Str()
    short_name = fields.Str()
    long_name = fields.Str()
    country = fields.Nested("CountrySchema", only=["short_name", "long_name"])
    localities = fields.Nested(
        "LocalitySchema", many=True, only=["short_name", "long_name", "id"]
    )


class CountrySchema(Schema):
    short_name = fields.Str()
    long_name = fields.Str()
    regions = fields.Nested(
        "RegionSchema", many=True, only=["short_name", "long_name", "id", "localities"]
    )


class PointSchema(Schema):
    place_id = fields.Str()
    lat = fields.Float()
    lng = fields.Float()
    name = fields.Str()
    # events = fields.Nested("EventSchema", only=["name", "id"], many=True)
    events = fields.List(fields.Dict())
    # events = fields.Nested(
    #    "EventDateSchema", only=["name", "event_id", "id"], many=True
    # )
