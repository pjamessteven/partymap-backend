from marshmallow import Schema, post_dump, fields, pre_dump
from pmapi.common.schemas import PaginatedSchema
from typemallow2 import ts_interface
from pmapi.common.schemas import TranslationHybridField

# from pmapi.media_item.schemas import MediaItemSchema


@ts_interface()
class FeaturedEventSchema(Schema):
    id = fields.Integer()
    next_date = fields.Nested("MiniEventDateSchema", attribute="next_event_date")


@ts_interface()
class MiniEventSchema(Schema):
    id = fields.Integer()
    name = fields.Str()
    host = fields.Nested("UserSchema", only=["username"])
    created_at = fields.DateTime()
    updated_at = fields.DateTime()
    description = fields.String()
    description_t = TranslationHybridField()
    youtube_url = fields.Str()
    tz = fields.Str()
    next_date = fields.Nested(
        "MiniEventDateSchema", attribute="next_event_date", exclude=["event"]
    )
    event_tags = fields.Nested("EventTagSchema", many=True)
    rrule = fields.Nested("RruleSchema")
    cover_items = fields.Nested("MediaItemSchema", many=True)
    hidden = fields.Boolean()
    is_favorited = fields.Boolean()
    page_views = fields.Int()

    @post_dump
    def remove_description_if_description_t_exists(self, data, **kwargs):
        if data.get("description_t"):
            data.pop("description", None)
        return data


@ts_interface()
class EventSchema(Schema):
    id = fields.Integer()
    name = fields.Str()
    creator = fields.Nested("UserSchema", only=["username"])
    host = fields.Nested("UserSchema", only=["username"])
    created_at = fields.DateTime()
    updated_at = fields.DateTime()
    description = fields.String()
    description_t = TranslationHybridField()
    description_attribute = fields.Str()
    full_description = fields.Str()
    full_description_t = TranslationHybridField()
    full_description_attribute = fields.Str()
    youtube_url = fields.Str()
    tz = fields.Str()
    event_dates = fields.Nested(
        "MiniEventDateSchema", many=True, attribute="event_dates", exclude=["event"]
    )
    next_date = fields.Nested(
        "EventDateSchema", attribute="next_event_date", exclude=["event"]
    )
    event_tags = fields.Nested("EventTagSchema", many=True)
    rrule = fields.Nested("RruleSchema")
    media_items = fields.Nested("MediaItemSchema", many=True)
    cover_items = fields.Nested("MediaItemSchema", many=True)
    hidden = fields.Boolean()
    last_transaction = fields.Nested("TransactionSchema")
    is_favorited = fields.Boolean()
    page_views = fields.Int()


@ts_interface()
class EventVersionSchema(Schema):
    changeset = fields.Dict()
    # previous = fields.Nested("EventVersionSchema", exclude=["previous"])
    index = fields.Integer()
    transaction = fields.Nested("TransactionSchema")
    transaction_id = fields.Integer()
    end_transaction_id = fields.Integer()
    id = fields.Integer()
    name = fields.Str()


class EventListSchema(PaginatedSchema):
    items = fields.Nested("EventSchema", many=True)


class MiniEventListSchema(PaginatedSchema):
    items = fields.Nested("MiniEventSchema", many=True)


class FeaturedEventListSchema(PaginatedSchema):
    items = fields.Nested("FeaturedEventSchema", many=True)


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
    items = fields.List(fields.Tuple((fields.Nested("UserSchema"), fields.String())))


 