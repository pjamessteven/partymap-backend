from marshmallow import fields
from marshmallow import Schema
from pmapi.common.schemas import PaginatedSchema
from pmapi.event_album.schemas import EventAlbumSchema


class EventSchema(Schema):
    id = fields.UUID()
    name = fields.Str()
    creator = fields.Nested("UserSchema", only=["username"])
    created_at = fields.DateTime()
    description = fields.Str()
    default_url = fields.Str()
    tz = fields.Str()
    event_dates = fields.Nested("EventDateSchema", many=True)
    event_albums = fields.Nested(EventAlbumSchema, many=True)
    event_tags = fields.Nested("EventTagSchema", many=True)
    rrule = fields.Nested("RruleSchema")
    featured_album = fields.Nested("EventAlbumSchema", only=["items"])
    cover_items = fields.Nested("AlbumItemSchema", many=True)


class EventListSchema(PaginatedSchema):
    items = fields.Nested("EventSchema", many=True)


class RruleSchema(Schema):
    recurring_type = fields.Integer()
    separation_count = fields.Integer()
    day_of_week = fields.Integer()
    week_of_month = fields.Integer()
    day_of_month = fields.Integer()
    month_of_year = fields.Integer()
