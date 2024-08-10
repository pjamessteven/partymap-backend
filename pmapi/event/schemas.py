from marshmallow import fields
from marshmallow import Schema
from pmapi.common.schemas import PaginatedSchema
from typemallow2 import ts_interface

# from pmapi.media_item.schemas import MediaItemSchema


@ts_interface()
class EventSchema(Schema):
    id = fields.Integer()
    name = fields.Str()
    creator = fields.Nested("UserSchema", only=["username"])
    host = fields.Nested("UserSchema", only=["username"])
    created_at = fields.DateTime()
    updated_at = fields.DateTime()
    description = fields.Str()
    description_attribute = fields.Str()
    full_description = fields.Str()
    full_description_attribute = fields.Str()
    youtube_url = fields.Str()
    tz = fields.Str()
    event_dates = fields.Nested(
        "MiniEventDateSchema", many=True, attribute="event_dates"
    )
    next_date = fields.Nested("EventDateSchema", attribute="next_event_date")
    event_tags = fields.Nested("EventTagSchema", many=True)
    rrule = fields.Nested("RruleSchema")
    media_items = fields.Nested("MediaItemSchema", many=True)
    cover_items = fields.Nested("MediaItemSchema", many=True)
    hidden = fields.Boolean()
    last_transaction = fields.Nested("TransactionSchema")
    is_favorited = fields.Boolean()
    page_views = fields.Int()
    event_reviews = fields.Nested("EventReviewSchema",
                                        many=True)


@ts_interface()
class EventVersionSchema(EventSchema):
    changeset = fields.Dict()
    # previous = fields.Nested("EventVersionSchema", exclude=["previous"])
    index = fields.Integer()
    transaction = fields.Nested("TransactionSchema")
    transaction_id = fields.Integer()
    end_transaction_id = fields.Integer()
    event_dates = fields.Nested(
        "EventDateSchema", many=True, exclude=["event"])


class EventListSchema(PaginatedSchema):
    items = fields.Nested("EventSchema", many=True)


class EventVersionListSchema(PaginatedSchema):
    items = fields.Nested("EventVersionSchema", many=True)


@ts_interface()
class RruleSchema(Schema):
    recurring_type = fields.Integer()
    separation_count = fields.Integer()
    day_of_week = fields.Integer()
    week_of_month = fields.Integer()
    day_of_month = fields.Integer()
    month_of_year = fields.Integer()
    # default_url = fields.Str()
    # default_location = fields.Nested("LocationSchema")
    start_date_time = fields.Str()
    end_date_time = fields.Str()
    exact = fields.Boolean()


@ts_interface()
class RruleVersionSchema(RruleSchema):
    changeset = fields.Dict()
    # previous = fields.Nested("EventVersionSchema", exclude=["previous"])
    index = fields.Integer()
    transaction = fields.Nested("TransactionSchema")
    transaction_id = fields.Integer()
    end_transaction_id = fields.Integer()


class ContributorListSchema(Schema):
    items = fields.List(fields.Tuple(
        (fields.Nested("UserSchema"), fields.String())))
