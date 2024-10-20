from marshmallow import fields, pre_dump
from marshmallow import Schema
from pmapi.event_location.model import EventLocation
from pmapi.event_location.schemas import LocationSchema, LocationVersionSchema
from pmapi.event_review.model import EventReview
from pmapi.event_review.schemas import EventReviewSchema, EventReviewVersionSchema
from typemallow2 import ts_interface
from pmapi.common.schemas import PaginatedJsonSchema, PaginatedSchema
from marshmallow_polyfield import PolyField
from pmapi.event.schemas import (
    EventSchema,
    EventVersionSchema,
    RruleSchema,
    RruleVersionSchema,
)
from pmapi.common.schemas import BlacklistedDict

from pmapi.event_artist.schemas import ArtistSchema, ArtistVersionSchema, EventDateArtistSchema, EventDateArtistVersionSchema
from pmapi.event_date.schemas import EventDateSchema, EventDateVersionSchema
from pmapi.event_tag.schemas import EventTagSchema, EventTagVersionSchema
from pmapi.event.model import Event, Rrule
from pmapi.event_date.model import EventDate
from pmapi.event_artist.model import Artist, EventDateArtist
from pmapi.event_tag.model import EventTag
from pmapi.media_item.model import MediaItem
from pmapi.media_item.schemas import MediaItemSchema, MediaItemVersionSchema
from pmapi.user.schemas import UserSchema

# from pmapi.media_item.schemas import MediaItemSchema


def schema_serialization_disambiguation(base_object, parent_obj):
    class_to_schema = {
        Event.__name__: EventSchema,
        EventDate.__name__: EventDateSchema,
        "EventVersion": EventVersionSchema,
        "EventDateVersion": EventDateVersionSchema,
        EventTag.__name__: EventTagSchema,
        "EventTagVersion": EventTagVersionSchema,
        EventDateArtist.__name__: EventDateArtistSchema,
        "EventDateArtistVersion": EventDateArtistVersionSchema,
        Artist.__name__: ArtistSchema,
        "ArtistVersion": ArtistVersionSchema,
        MediaItem.__name__: MediaItemSchema,
        "MediaItemVersion": MediaItemVersionSchema,
        Rrule.__name__: RruleSchema,
        "RruleVersion": RruleVersionSchema,
        "EventLocationVersion": LocationVersionSchema,
        EventLocation.__name__: LocationSchema,
        "EventReviewVersion": EventReviewVersionSchema,
        EventReview.__name__: EventReviewSchema,
    }
    try:
        return class_to_schema[base_object.__class__.__name__]()
    except KeyError:
        pass

    raise TypeError("Could not detect type. ")


@ts_interface()
class TransactionSchema(Schema):
    id = fields.Integer()
    issued_at = fields.DateTime()
    user = fields.Nested(UserSchema, only=["username"])

@ts_interface()
# marshmallow_polyfield not supported by typemallow2?
class ActivitySchema(Schema):
    id = fields.Integer()
    transaction_id = fields.Integer()
    target_id = fields.Integer()
    target_tx_id = fields.Integer()
    actor = fields.Nested(UserSchema, only=["username"])
    transaction = fields.Nested(TransactionSchema, attribute="transaction")
    changeset = BlacklistedDict(blacklist="geo", attribute="object_version.changeset")
    verb = fields.Str()
    object_type = fields.Str()
    target_type = fields.Str()
    object_version_id = fields.Str()
    object_version = PolyField(
        serialization_schema_selector=schema_serialization_disambiguation,
    )
    target_version = PolyField(
        serialization_schema_selector=schema_serialization_disambiguation,
    )
    """

    previous_version = PolyField(
        serialization_schema_selector=schema_serialization_disambiguation,
        attribute="object_version.previous",
    )
    previous_target_version = PolyField(
        serialization_schema_selector=schema_serialization_disambiguation,
        attribute="target_version.previous",
    )
    target_version_tx_id = fields.Integer(attribute="target_version.transaction_id")
    
    version_index = fields.Integer(attribute="object_version.index")
    """
    data = fields.Dict()

@ts_interface()
class TransactionActivitiesSchema(Schema):
    issued_at = fields.DateTime()
    username = fields.String()
    transaction_id = fields.Integer()
    activities = fields.List(
        (fields.Nested("ActivitySchema", exclude=["transaction"])))
    target_version = PolyField(
        serialization_schema_selector=schema_serialization_disambiguation,
    )
    target_type = fields.String()
    target_id = fields.Integer()
    
@ts_interface()
class PaginatedTransactionActivitiesSchema(PaginatedJsonSchema):
    items = fields.List(
        (fields.Nested("TransactionActivitiesSchema")))


class ActivityListSchema(PaginatedSchema):
    items = fields.Nested("ActivitySchema", many=True)
