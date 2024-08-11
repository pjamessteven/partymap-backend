from marshmallow import fields
from marshmallow import Schema
from pmapi.common.schemas import PaginatedSchema
from typemallow2 import ts_interface


@ts_interface()
class EventDateTicketSchema(Schema):
    id = fields.Integer()
    url = fields.Str()
    description = fields.Str()
    price_min = fields.Integer()
    price_max = fields.Integer()
    price_currency_code = fields.Str()


@ts_interface()
class EventDateSchema(Schema):
    id = fields.Integer()
    event_id = fields.Integer()
    name = fields.Str(attribute="event.name")
    start = fields.Str(attribute="start")
    end = fields.Str(attribute="end")
    start_naive = fields.Str(attribute="start_naive")
    end_naive = fields.Str(attribute="end_naive")
    date_confirmed = fields.Boolean()
    tz = fields.Str()
    location = fields.Nested("LocationSchema", exclude=["event_dates"])
    location_id = fields.Str()
    event = fields.Nested(
        "EventSchema",
        only=["event_tags", "cover_items", "host", "rrule", "description"],
    )
    media_items = fields.Nested("MediaItemSchema", many=True)
    description = fields.Str()
    description_attribute = fields.Str()
    url = fields.Str()
    tickets = fields.Nested("EventDateTicketSchema", many=True)
    tz = fields.Str()
    cancelled = fields.Boolean()
    distance = fields.Float()
    duration = fields.Float()
    size = fields.Integer()
    artists = fields.Nested("EventDateArtistSchema", many=True)
    user_going = fields.Boolean()
    user_interested = fields.Boolean()


@ts_interface()
class MiniEventDateSchema(Schema):
    id = fields.Integer()
    event_id = fields.Integer()
    name = fields.Str(attribute="event.name")
    event = fields.Nested(
        "EventSchema",
        only=["event_tags", "cover_items", "host", "rrule", "description"],
    )
    start = fields.Str(attribute="start")
    end = fields.Str(attribute="end")
    start_naive = fields.Str(attribute="start_naive")
    end_naive = fields.Str(attribute="end_naive")
    date_confirmed = fields.Boolean()
    tz = fields.Str()
    user_going = fields.Boolean()
    user_interested = fields.Boolean()
    location = fields.Nested("LocationSchema", exclude=["event_dates"])
    location_id = fields.Str()
    distance = fields.Float()


@ts_interface()
class EventDateVersionSchema(Schema):
    id = fields.Integer()
    event_id = fields.Integer()
    name = fields.Str(attribute="event.name")
    start_naive = fields.Str(attribute="start_naive")
    end_naive = fields.Str(attribute="end_naive")
    changeset = fields.Dict()
    index = fields.Integer()
    transaction = fields.Nested("TransactionSchema")
    transaction_id = fields.Integer()
    end_transaction_id = fields.Integer()


class EventDateListSchema(PaginatedSchema):
    items = fields.Nested("EventDateSchema", many=True)


class EventDateQueryListSchema(PaginatedSchema):
    items = fields.List(fields.Tuple(
        (fields.Nested("MiniEventDateSchema"), fields.Str())))
    radius = fields.Integer()
    top_artists = fields.Nested("MinimalEventDateArtistSchema", many=True)
    top_tags = fields.Nested("EventTagSchema", many=True)
