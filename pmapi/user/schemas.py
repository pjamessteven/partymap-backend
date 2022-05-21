from marshmallow import fields
from marshmallow import Schema
from pmapi.common.schemas import PaginatedSchema


class UserSchema(Schema):
    username = fields.Str()
    role = fields.Int()
    id = fields.UUID()
    version_count = fields.Int()
    hosted_events = fields.Nested("EventSchema", many=True)
    created_events = fields.Nested("EventSchema", many=True)
    version_count = fields.Int()
    created_at = fields.DateTime()


class UserListSchema(PaginatedSchema):
    items = fields.Nested("UserSchema", many=True)


class PrivateUserSchema(UserSchema):
    # this information should only be visible to current user
    email = fields.Str()
    status = fields.Str()
    pw_enabled = fields.Function(lambda obj: True if obj.password else False)
    oauth = fields.Boolean()
    oauth_obj = fields.Nested("OAuth")
    last_active = fields.DateTime()


class OAuth(Schema):
    provider_user_id = fields.Str()
    user_id = fields.UUID()
    created_at = fields.DateTime()
    token = fields.Dict()
