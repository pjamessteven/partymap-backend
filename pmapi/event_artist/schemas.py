from marshmallow import fields
from marshmallow import Schema
from pmapi.common.schemas import PaginatedSchema
from typemallow2 import ts_interface


@ts_interface()
class ArtistSchema(Schema):
    id = fields.Int()
    name = fields.Str()
    area = fields.Str()
    mbid = fields.Str()
    created_at = fields.DateTime()
    description = fields.Str()
    popularity = fields.Int()
    disambiguation = fields.Str()
    urls = fields.Nested("ArtistUrlSchema", many=True)
    tags = fields.Nested("ArtistTagSchema", many=True, attribute="artist_tags")
    # events_with_tag?
    future_event_dates = fields.Nested(
        "EventDateSchema", many=True, exclude=["artists"]
    )
    past_event_dates = fields.Nested(
        "EventDateSchema", many=True, exclude=["artists"])
    event_count = fields.Int()
    media_items = fields.Nested("MediaItemSchema", many=True)



class ArtistListSchema(PaginatedSchema):
    items = fields.Nested(
        ArtistSchema, many=True, exclude=["future_event_dates", "past_event_dates"]
    )


@ts_interface()
class ArtistUrlSchema(Schema):
    url = fields.Str()
    type = fields.Str()


@ts_interface()
class ArtistTagSchema(Schema):
    tag = fields.Str(attribute="tag_id")


@ts_interface()
class EventDateArtistSchema(Schema):
    description = fields.Pluck(
        "ArtistSchema", "description", attribute="artist", dump_only=True
    )
    disambiguation = fields.Pluck(
        "ArtistSchema", "disambiguation", attribute="artist", dump_only=True
    )
    name = fields.Pluck("ArtistSchema", "name",
                        attribute="artist", dump_only=True)
    popularity = fields.Pluck(
        "ArtistSchema", "popularity", attribute="artist", dump_only=True
    )
    area = fields.Pluck("ArtistSchema", "area",
                        attribute="artist", dump_only=True)
    mbid = fields.Pluck("ArtistSchema", "mbid",
                        attribute="artist", dump_only=True)
    urls = fields.Pluck("ArtistSchema", "urls",
                        attribute="artist", dump_only=True)
    media_items = fields.Pluck(
        "ArtistSchema", "media_items", attribute="artist", dump_only=True
    )
    artist_id = fields.Pluck("ArtistSchema", "id",
                             attribute="artist", dump_only=True)
    id = fields.Int()
    start_naive = fields.Str()
    stage = fields.Str()

@ts_interface()
class ArtistVersionSchema(Schema):
    changeset = fields.Dict()
    id = fields.Int()
    # previous = fields.Nested("MediaItemVersionSchema", exclude=["previous"])
    index = fields.Integer()
    transaction = fields.Nested("TransactionSchema")
    transaction_id = fields.Integer()
    # end_transaction_id = fields.Integer()

@ts_interface()
class EventDateArtistVersionSchema(Schema):
    changeset = fields.Dict()
    name = fields.Pluck("ArtistSchema", "name",
                    attribute="artist", dump_only=True)
    id = fields.Int()
    # previous = fields.Nested("MediaItemVersionSchema", exclude=["previous"])
    index = fields.Integer()
    transaction = fields.Nested("TransactionSchema")
    transaction_id = fields.Integer()
    # end_transaction_id = fields.Integer()


class MinimalEventDateArtistSchema(Schema):
    name = fields.Pluck("ArtistSchema", "name",
                        attribute="artist", dump_only=True)
    disambiguation = fields.Pluck(
        "ArtistSchema", "disambiguation", attribute="artist", dump_only=True
    )
    area = fields.Pluck("ArtistSchema", "area",
                        attribute="artist", dump_only=True)
    id = fields.Pluck("ArtistSchema", "id",
                      attribute="artist", dump_only=True)
    media_items = fields.Pluck(
        "ArtistSchema", "media_items", attribute="artist", dump_only=True
    )
