from marshmallow import fields
from marshmallow import Schema
from typemallow2 import ts_interface

# from pmapi.event.schemas import EventSchema


@ts_interface()
class EventReviewSchema(Schema):
    id = fields.Integer()
    event_id = fields.Integer()
    event_date_id = fields.Integer()
    text = fields.Str()
    media_items = fields.Nested("MediaItemSchema", many=True)
    creator = fields.Nested("UserSchema", only=["username"])
    created_at = fields.DateTime()
    score = fields.Integer()
    rating = fields.Integer()

@ts_interface()
class EventReviewVersionSchema(EventReviewSchema):
    changeset = fields.Dict()
    index = fields.Integer()
    transaction = fields.Nested("TransactionSchema")
    transaction_id = fields.Integer()

