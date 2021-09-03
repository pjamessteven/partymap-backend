from marshmallow import fields
from marshmallow import Schema
from pmapi.common.schemas import PaginatedSchema

# from pmapi.event.schemas import EventSchema


class EventDateSchema(Schema):
    id = fields.UUID()
    event_id = fields.UUID()
    name = fields.Str(attribute="event.name")
    start = fields.Str(attribute="start")
    end = fields.Str(attribute="end")
    start_naive = fields.Str(attribute="start_naive")
    end_naive = fields.Str(attribute="end_naive")
    tz = fields.Str()
    location = fields.Nested("LocationSchema", exclude=["event_dates"])
    event = fields.Nested("EventSchema", only=["event_tags", "cover_items"])
    description = fields.Str()
    url = fields.Str()
    ticket_url = fields.Str()
    tz = fields.Str()
    cancelled = fields.Boolean()
    distance = fields.Float()
    duration = fields.Float()
    size = fields.Integer()


class EventDateListSchema(PaginatedSchema):
    items = fields.Nested("EventDateSchema", many=True)
