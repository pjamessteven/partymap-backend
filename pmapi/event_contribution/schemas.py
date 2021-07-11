from marshmallow import fields
from marshmallow import Schema

# from pmapi.event.schemas import EventSchema


class EventContributionSchema(Schema):
    id = fields.UUID()
    event_id = fields.UUID()
    text = fields.Str()
    images = fields.Nested("AlbumItemSchema", many=True)
    creator = fields.Nested("UserSchema", only=["username"])
    created_at = fields.DateTime()
    score = fields.Integer()
