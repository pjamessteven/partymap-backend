from marshmallow import fields
from marshmallow import Schema
from sqlalchemy_utils import TranslationHybrid


class PaginatedSchema(Schema):
    has_next = fields.Bool()
    has_prev = fields.Bool()
    page = fields.Int()
    pages = fields.Int()
    per_page = fields.Int()
    next_num = fields.Int()
    prev_num = fields.Int()
    total = fields.Int()

class PaginatedJsonSchema(Schema):
    has_next = fields.Bool()
    has_prev = fields.Bool()
    page = fields.Int()
    pages = fields.Int()
    per_page = fields.Int()
    total = fields.Int()

class BlacklistedDict(fields.Dict):
    def __init__(self, blacklist, **kwargs):
        super(BlacklistedDict, self).__init__(**kwargs)
        self.blacklist = blacklist

    def _serialize(self, value, attr, obj):
        value = super(BlacklistedDict, self)._serialize(value, attr, obj)
        return {key: value[key] for key in value if key not in self.blacklist}

    def _deserialize(self, value, attr, obj):
        value = super(BlacklistedDict, self)._deserialize(value, attr, obj)
        return {key: value[key] for key in value if key not in self.blacklist}

class TranslationHybridField(fields.Field):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _serialize(self, value, attr, obj, **kwargs):
        if isinstance(value, TranslationHybrid):
            return value.current
        return value

    def _deserialize(self, value, attr, data, **kwargs):
        return value
