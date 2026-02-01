from marshmallow import fields
from marshmallow import Schema
from typemallow2 import ts_interface
from pmapi.common.schemas import PaginatedSchema, TranslationHybridField

# from pmapi.event.schemas import EventSchema

@ts_interface()
class EventReviewListSchema(PaginatedSchema):
    items = fields.Nested("EventReviewSchema", many=True)

@ts_interface()
class EventReviewSchema(Schema):
    id = fields.Integer()
    event_id = fields.Integer()
    event_date_id = fields.Integer()
    text = fields.Str()
    text_t = TranslationHybridField()
    media_items = fields.Nested("MediaItemSchema", many=True)
    creator = fields.Nested("UserSchema", only=["username"])
    created_at = fields.DateTime()
    score = fields.Integer()
    rating = fields.Integer()
    children = fields.Nested("self", many=True) # This is the crucial line
    
@ts_interface()
class EventReviewVersionSchema(Schema):
    text = fields.Str()
    id = fields.Integer()
    event_id = fields.Integer()
    event_date_id = fields.Integer()
    rating = fields.Integer()

    changeset = fields.Dict()
    index = fields.Integer()
    transaction = fields.Nested("TransactionSchema")
    transaction_id = fields.Integer()

