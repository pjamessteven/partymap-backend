from marshmallow import fields
from marshmallow import Schema
from pmapi.common.schemas import PaginatedSchema
from typemallow2 import ts_interface

class ReportSchema(Schema):
    id = fields.UUID()
    creator = fields.Nested("UserSchema", only=["username"])
    created_at = fields.DateTime()
    open = fields.Boolean()
    description = fields.Str()

    event = fields.Nested("EventSchema")
    event_contribution = fields.Nested("EventContributionSchema")
    media_item = fields.Nested("MediaItemSchema")


class ReportListSchema(PaginatedSchema):
    items = fields.Nested("ReportSchema", many=True)
