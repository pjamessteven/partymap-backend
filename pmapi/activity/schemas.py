from marshmallow import fields
from marshmallow import Schema
from pmapi.common.schemas import PaginatedSchema
from marshmallow_polyfield import PolyField
from pmapi.event.schemas import (
    EventSchema,
    EventVersionSchema,
    RruleSchema,
    RruleVersionSchema,
)
from pmapi.event_artist.schemas import EventDateArtistSchema
from pmapi.event_date.schemas import EventDateSchema, EventDateVersionSchema
from pmapi.event_tag.schemas import EventTagSchema
from pmapi.event.model import Event, Rrule
from pmapi.event_date.model import EventDate
from pmapi.event_artist.model import EventDateArtist
from pmapi.event_tag.model import EventTag
from pmapi.media_item.model import MediaItem
from pmapi.media_item.schemas import MediaItemSchema, MediaItemVersionSchema

# from pmapi.media_item.schemas import MediaItemSchema


def schema_serialization_disambiguation(base_object, parent_obj):
    class_to_schema = {
        Event.__name__: EventSchema,
        EventDate.__name__: EventDateSchema,
        "EventVersion": EventVersionSchema,
        "EventDateVersion": EventDateVersionSchema,
        EventTag.__name__: EventTagSchema,
        "EventTagVersion": EventTagSchema,
        EventDateArtist.__name__: EventDateArtistSchema,
        "EventDateArtistVersion": EventDateArtistSchema,
        MediaItem.__name__: MediaItemSchema,
        "MediaItemVersion": MediaItemVersionSchema,
        Rrule.__name__: RruleSchema,
        "RruleVersion": RruleVersionSchema,
    }
    try:
        return class_to_schema[base_object.__class__.__name__]()
    except KeyError:
        pass

    raise TypeError("Could not detect type. ")


class TransactionSchema(Schema):
    id = fields.Integer()
    issued_at = fields.DateTime()
    user = fields.Nested("UserSchema", only=["username"])


class ActivitySchema(Schema):
    id = fields.Integer()
    actor = fields.Nested("UserSchema", only=["username"])
    transaction = fields.Nested(TransactionSchema, attribute="transaction")
    changeset = fields.Dict(attribute="object_version.changeset")
    verb = fields.Str()
    object_type = fields.Str()
    object_version = PolyField(
        serialization_schema_selector=schema_serialization_disambiguation,
    )
    target_version = PolyField(
        serialization_schema_selector=schema_serialization_disambiguation,
    )
    previous_target_version = PolyField(
        serialization_schema_selector=schema_serialization_disambiguation,
        attribute="target_version.previous",
    )
    target_version_tx_id = fields.Integer(attribute="target_version.transaction_id")
    version_index = fields.Integer(attribute="object_version.index")
    data = fields.Dict()


class ActivityListSchema(PaginatedSchema):
    items = fields.Nested("ActivitySchema", many=True)
