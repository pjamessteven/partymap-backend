from marshmallow import fields
from marshmallow import Schema
from pmapi.common.schemas import PaginatedSchema
from flask import current_app
import os


class EventAlbumSchema(Schema):
    id = fields.UUID()
    creator_id = fields.UUID()
    created_at = fields.DateTime()
    name = fields.Str()
    caption = fields.Str()
    images = fields.Nested("EventImageSchema", many=True)


class EventImageSchema(Schema):
    id = fields.UUID()
    creator_id = fields.UUID()
    created_at = fields.DateTime()
    filename = fields.Str()
    thumb_filename = fields.Str()
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
