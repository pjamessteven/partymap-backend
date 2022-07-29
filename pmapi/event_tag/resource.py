import json
from flask import Blueprint
from flask_apispec import doc
from flask_apispec import marshal_with
from flask_apispec import MethodResource
from flask_apispec import use_kwargs
from marshmallow import fields

from pmapi.common.controllers import paginated_view_args
from .schemas import TagListSchema
import pmapi.event_tag.controllers as event_tags

event_tags_blueprint = Blueprint("tags", __name__)


@doc(tags=["tags"])
class TagsResource(MethodResource):
    @doc(summary="Query event tags", description="Query all event tags")
    @use_kwargs(
        {
            "tag_name": fields.Str(required=False, allow_none=True),
            "date_min": fields.DateTime(required=False),
            "date_max": fields.DateTime(required=False),
            "radius": fields.Int(),
            "location": fields.Str(),
            **paginated_view_args(sort_options=["count", "created_at"]),
        },
    )
    @marshal_with(TagListSchema(), code=200)
    def get(self, **kwargs):
        if kwargs.get("location"):
            kwargs["location"] = json.loads(kwargs["location"])
        return event_tags.get_event_tags(**kwargs)


event_tags_blueprint.add_url_rule("/", view_func=TagsResource.as_view("TagsResource"))
