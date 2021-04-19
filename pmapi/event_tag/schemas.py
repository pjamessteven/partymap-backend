from marshmallow import fields
from marshmallow import Schema
from pmapi.common.schemas import PaginatedSchema


class TagSchema(Schema):
    tag = fields.Str()
    count = fields.Integer()
    # events_with_tag?


class TagListSchema(PaginatedSchema):
    items = fields.Nested(TagSchema, many=True)


class EventTagSchema(Schema):
    tag = fields.Str(attribute="tag_id")
