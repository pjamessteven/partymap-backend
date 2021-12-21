from marshmallow import fields
from marshmallow import Schema
from pmapi.common.schemas import PaginatedSchema

# from pmapi.media_item.schemas import MediaItemSchema


class SuggestedEditSchema(Schema):
    id = fields.Integer()
    created_at = fields.DateTime()
    creator = fields.Nested("UserSchema", only=["username"])
    event_date_id = fields.Integer()
    event_id = fields.Integer()
    action = fields.Str()
    kwargs = fields.Dict()
    message = fields.Str()
    object_type = fields.Str()
    status = fields.Str()
    approved_by = fields.Nested("UserSchema", only=["username"])


class SuggestedEditListSchema(PaginatedSchema):
    items = fields.Nested("SuggestedEditSchema", many=True)
