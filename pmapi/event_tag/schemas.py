from marshmallow import fields
from marshmallow import Schema
from pmapi.common.schemas import PaginatedSchema
from typemallow2 import ts_interface
from pmapi.common.schemas import TranslationHybridField

@ts_interface()
class TagSchema(Schema):
    tag = fields.Str()
    tag_t = TranslationHybridField()

    count = fields.Integer()
    # events_with_tag?

class TagListSchema(PaginatedSchema):
    items = fields.Nested(TagSchema, many=True)

@ts_interface()
class EventTagSchema(Schema):
    tag = fields.Str(attribute="tag.tag")
    tag_t = TranslationHybridField(attribute="tag.tag_t")

class EventTagVersionSchema(EventTagSchema):
    changeset = fields.Dict()
    index = fields.Integer()
    transaction = fields.Nested("TransactionSchema")
    transaction_id = fields.Integer()
