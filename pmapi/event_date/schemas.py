from marshmallow import fields
from marshmallow import Schema
from pmapi.common.schemas import PaginatedSchema
from pmapi.event_tag.schemas import EventTagSchema

# from pmapi.event.schemas import EventSchema


class EventDateSchema(Schema):
    id = fields.UUID()
    event_id = fields.UUID()
    name = fields.Str(attribute="event.name")
    start = fields.Str(attribute="event_start")
    end = fields.Str(attribute="event_end")
    start_naive = fields.Str(attribute="event_start_naive")
    end_naive = fields.Str(attribute="event_end_naive")
    tz = fields.Str()
    tags = fields.Nested(EventTagSchema, many=True)
    location = fields.Nested("LocationSchema", exclude=["event_dates"])
    # event = fields.Nested(EventSchema, exclude=["event_dates"])


class EventDateListSchema(PaginatedSchema):
    items = fields.Nested("EventDateSchema", many=True)
