from marshmallow import fields
from marshmallow import Schema
from pmapi.common.schemas import PaginatedSchema
from pmapi.event_image.schemas import EventImageSchema


class EventSchema(Schema):
    id = fields.UUID()
    name = fields.Str()
    creator_id = fields.UUID()
    created_at = fields.DateTime()
    description = fields.Str()
    default_url = fields.Str()
    tz = fields.Str()
    event_dates = fields.Nested("EventDateSchema", many=True)
    event_images = fields.Nested(EventImageSchema, many=True)
    event_tags = fields.Nested("EventTagSchema")
    rrule = fields.Nested("RruleSchema")


class EventListSchema(PaginatedSchema):
    items = fields.Nested("EventSchema", many=True)


class RruleSchema(Schema):
    recurring_type = fields.Integer()
    separation_count = fields.Integer()
    day_of_week = fields.Integer()
    week_of_month = fields.Integer()
    day_of_month = fields.Integer()
    month_of_year = fields.Integer()
