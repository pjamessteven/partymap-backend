from marshmallow import fields
from marshmallow import Schema
from pmapi.common.schemas import PaginatedSchema
from typemallow2 import ts_interface

@ts_interface()
class ReportSchema(Schema):
    id = fields.UUID()
    creator = fields.Nested("PrivateUserSchema", only=["username", "email"])
    created_at = fields.DateTime()
    open = fields.Boolean()
    message = fields.Str()
    email = fields.Str()
    event = fields.Nested("EventSchema", only=["name", "id", "host"])
    event_review = fields.Nested("EventReviewSchema")
    media_item = fields.Nested("MediaItemSchema")


class ReportListSchema(PaginatedSchema):
    items = fields.Nested("ReportSchema", many=True)
