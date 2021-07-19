from marshmallow import fields
from marshmallow import Schema


class UserSchema(Schema):
    username = fields.Str()
    email = fields.Email()
    status = fields.Str()
    role = fields.Int()
    id = fields.UUID()
    pw_enabled = fields.Function(lambda obj: True if obj.password else False)
    oauth = fields.Boolean()
