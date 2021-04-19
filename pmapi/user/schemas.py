from marshmallow import fields
from marshmallow import Schema


class UserSchema(Schema):
    username = fields.Str()
    email = fields.Email()
    status = fields.Str()
    role = fields.Int()
    id = fields.UUID()
