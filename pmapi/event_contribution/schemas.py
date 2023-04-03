from marshmallow import fields
from marshmallow import Schema
from typemallow2 import ts_interface

# from pmapi.event.schemas import EventSchema

@ts_interface()
class EventContributionSchema(Schema):
    id = fields.UUID()
    event_id = fields.Integer()
    text = fields.Str()
    images = fields.Nested("AlbumItemSchema", many=True)
    creator = fields.Nested("UserSchema", only=["username"])
    created_at = fields.DateTime()
    score = fields.Integer()
