from marshmallow import fields
from marshmallow import Schema


class PaginatedSchema(Schema):
    has_next = fields.Bool()
    has_prev = fields.Bool()
    page = fields.Int()
    pages = fields.Int()
    per_page = fields.Int()
    next_num = fields.Int()
    prev_num = fields.Int()
    total = fields.Int()
