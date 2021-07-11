from marshmallow import fields
from marshmallow import Schema
from pmapi.common.schemas import PaginatedSchema
from flask import current_app
import os


class EventAlbumSchema(Schema):
    id = fields.UUID()
    creator = fields.Nested("UserSchema", only=["username"])
    created_at = fields.DateTime()
    name = fields.Str()
    caption = fields.Str()
    items = fields.Nested("AlbumItemSchema", many=True)


class AlbumItemSchema(Schema):
    id = fields.UUID()
    creator = fields.Nested("UserSchema", only=["username"])
    created_at = fields.DateTime()
    filename = fields.Str()
    thumb_filename = fields.Str()
    position = fields.Int()
    caption = fields.Str()
    url = fields.Function(
        lambda obj: os.path.join(
            current_app.config["UPLOADS_URL"] + str("album/") + str(obj.album_id),
            obj.filename,
        ),
    )
    thumb_url = fields.Function(
        lambda obj: os.path.join(
            current_app.config["UPLOADS_URL"] + str("album/") + str(obj.album_id),
            obj.thumb_filename,
        )
    )


class EventImageListSchema(PaginatedSchema):
    items = fields.Nested("EventImageSchema", many=True)
