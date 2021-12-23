from marshmallow import fields
from marshmallow import Schema
from pmapi.common.schemas import PaginatedSchema

from pmapi.event_artist.schemas import EventDateArtistSchema


class EventDateSchema(Schema):
    id = fields.Integer()
    event_id = fields.Integer()
    name = fields.Str(attribute="event.name")
    start = fields.Str(attribute="start")
    end = fields.Str(attribute="end")
    start_naive = fields.Str(attribute="start_naive")
    end_naive = fields.Str(attribute="end_naive")
    tz = fields.Str()
    location = fields.Nested("LocationSchema", exclude=["event_dates"])
    location_id = fields.Str()
    event = fields.Nested("EventSchema", only=["event_tags", "cover_items", "host"])
    description = fields.Str()
    description_attribute = fields.Str()
    url = fields.Str()
    # ticket_url = fields.Str()
    tz = fields.Str()
    cancelled = fields.Boolean()
    distance = fields.Float()
    duration = fields.Float()
    size = fields.Integer()
    artists = fields.Nested(EventDateArtistSchema, many=True)


class EventDateVersionSchema(EventDateSchema):
    changeset = fields.Dict()
    previous = fields.Nested("EventDateVersionSchema", exclude=["previous"])
    index = fields.Integer()
    transaction = fields.Nested("TransactionSchema")
    transaction_id = fields.Integer()
    end_transaction_id = fields.Integer()


class EventDateListSchema(PaginatedSchema):
    items = fields.Nested("EventDateSchema", many=True)
