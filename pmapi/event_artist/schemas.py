from marshmallow import fields
from marshmallow import Schema
from pmapi.common.schemas import PaginatedSchema


class ArtistSchema(Schema):
    id = fields.Int()
    name = fields.Str()
    area = fields.Str()
    mbid = fields.Str()
    description = fields.Str()
    disambiguation = fields.Str()
    urls = fields.Nested("ArtistUrlSchema", many=True)
    # events_with_tag?


class ArtistListSchema(PaginatedSchema):
    items = fields.Nested(ArtistSchema, many=True)


class ArtistUrlSchema(Schema):
    url = fields.Str()
    type = fields.Str()


class EventDateArtistSchema(Schema):
    description = fields.Pluck(
        "ArtistSchema", "description", attribute="artist", dump_only=True
    )
    disambiguation = fields.Pluck(
        "ArtistSchema", "disambiguation", attribute="artist", dump_only=True
    )
    name = fields.Pluck("ArtistSchema", "name", attribute="artist", dump_only=True)
    area = fields.Pluck("ArtistSchema", "area", attribute="artist", dump_only=True)
    mbid = fields.Pluck("ArtistSchema", "mbid", attribute="artist", dump_only=True)
    urls = fields.Pluck("ArtistSchema", "urls", attribute="artist", dump_only=True)
    artist_id = fields.Pluck("ArtistSchema", "id", attribute="artist", dump_only=True)
    id = fields.Int()
    start_naive = fields.Str()
