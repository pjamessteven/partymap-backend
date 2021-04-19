from marshmallow import fields
from marshmallow import Schema
from pmapi.common.schemas import PaginatedSchema


class EventImageSchema(Schema):
    id = fields.UUID()
    creator_id = fields.UUID()
    created_at = fields.DateTime()
    filename = fields.Str()
    thumb_filename = fields.Str()
    caption = fields.Str()


class EventImageListSchema(PaginatedSchema):
    items = fields.Nested("EventImageSchema", many=True)
