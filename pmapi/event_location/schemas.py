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
    country_code = fields.Str()
    country = fields.Str()
    city = fields.Str()
    address_components = fields.Str()
    place_id = fields.Str()
    event_dates = fields.Nested(EventDateSchema, many=True)


class LocationListSchema(PaginatedSchema):
    items = fields.Nested("LocationSchema", many=True)


class PointSchema(Schema):
    place_id = fields.Str()
    lat = fields.Float()
    lng = fields.Float()
    name = fields.Str()
    events = fields.Nested("EventSchema", only=["name", "id"], many=True)
