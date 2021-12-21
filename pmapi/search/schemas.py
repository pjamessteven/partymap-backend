from marshmallow import fields
from marshmallow import Schema

# from pmapi.media_item.schemas import MediaItemSchema


class SearchSchema(Schema):
    results = fields.List(fields.Dict())
