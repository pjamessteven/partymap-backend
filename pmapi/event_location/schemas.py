from marshmallow import fields
from marshmallow import Schema
from pmapi.common.schemas import BlacklistedDict
from typemallow2 import ts_interface
from pmapi.common.schemas import PaginatedSchema
from pmapi.event_date.schemas import EventDateSchema

@ts_interface()
class LocationSchema(Schema):
    lat = fields.Float()
    lng = fields.Float()
    name = fields.Str()
    description = fields.Str()
    country = fields.Nested('CountrySchema', only=['short_name'])
    city = fields.Str()
    place_id = fields.Str()
    event_dates = fields.Nested(EventDateSchema, many=True)

    locality = fields.Method("get_general_location_string")

    def get_general_location_string(self, obj):
        country = getattr(obj, "country")

        locality = getattr(obj, "locality", None)
        region = getattr(obj, "region", None)

        loc_name = getattr(locality, "long_name", None)
        
        if not loc_name: 
            loc_name = getattr(obj, "name", None)
        # countries that are better reprented by their states
        if country.short_name == "US" or country.short_name == "GB":
            return f"{loc_name}, {region.long_name}"
        elif country:
            return f"{loc_name}, {country.long_name}"
        else:
            return loc_name or getattr(obj, "name", None)

class LocationVersionSchema(Schema):
    description = fields.Str()
    changeset = BlacklistedDict(blacklist="geo", attribute="object_version.changeset")
    index = fields.Integer()
    transaction = fields.Nested("TransactionSchema")
    transaction_id = fields.Integer()

class LocationListSchema(PaginatedSchema):
    items = fields.Nested("LocationSchema", many=True)

@ts_interface()
class LocalitySchema(Schema):
    id = fields.Str()
    short_name = fields.Str()
    long_name = fields.Str()
    country = fields.Nested("CountrySchema", only=["short_name", "long_name"])
    region = fields.Nested("RegionSchema", only=["short_name", "long_name", "id"])


@ts_interface()
class RegionSchema(Schema):
    id = fields.Str()
    short_name = fields.Str()
    long_name = fields.Str()
    localities = fields.Nested(
        "LocalitySchema", many=True, only=["short_name", "long_name", "id"]
    )
    event_count = fields.Int()


class ExtendedRegionSchema(RegionSchema):
    lat = fields.Float()
    lng = fields.Float()

@ts_interface()
class CountrySchema(Schema):
    short_name = fields.Str()
    long_name = fields.Str()
    event_count = fields.Int()

@ts_interface()
class PointSchema(Schema):
    place_id = fields.Str()
    lat = fields.Float()
    lng = fields.Float()
    name = fields.Str()
    # events = fields.Nested("EventSchema", only=["name", "id"], many=True)
    events = fields.List(fields.Dict())
    # events = fields.Nested(
    #    "EventDateSchema", only=["name", "event_id", "id"], many=True
    # )
