from marshmallow import fields
from marshmallow import Schema
from pmapi.common.schemas import PaginatedSchema
from pmapi.event.schemas import EventSchema
from typemallow2 import ts_interface


@ts_interface()
class OAuth(Schema):
    provider_user_id = fields.Str()
    user_id = fields.UUID()
    created_at = fields.DateTime()
    token = fields.Dict()


@ts_interface()
class UserSchema(Schema):
    username = fields.Str()
    role = fields.Int()
    id = fields.UUID()
    version_count = fields.Int()
    created_at = fields.DateTime()
    avatar = fields.Nested("MediaItemSchema")
    description = fields.Str()
    alias = fields.Str()


class UserListSchema(PaginatedSchema):
    items = fields.Nested("UserSchema", many=True)


@ts_interface()
class PrivateUserSchema(UserSchema):
    # this information extends the general user schema, but should only be visible to current user
    email = fields.Str()
    status = fields.Str()
    pw_enabled = fields.Function(lambda obj: True if obj.password else False)
    oauth = fields.Boolean()
    oauth_obj = fields.Nested(OAuth)
    last_active = fields.DateTime()
    locale = fields.Str()