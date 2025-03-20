import json
from flask import Blueprint, jsonify, request
from flask_login import login_required
from flask_apispec import doc
from flask_apispec import marshal_with
from flask_apispec import MethodResource
from flask_apispec import use_kwargs
from marshmallow import fields
from pmapi.common.permissions import current_user_role_is_at_least
from pmapi.exceptions import InvalidPermissions

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
            "has_translation": fields.Boolean(),
            **paginated_view_args(sort_options=["count", "created_at"]),
        },
        location="query"
    )
    @marshal_with(TagListSchema(), code=200)
    def get(self, **kwargs):
        if kwargs.get("location"):
            kwargs["location"] = json.loads(kwargs["location"])
        return event_tags.get_event_tags(**kwargs)


event_tags_blueprint.add_url_rule(
    "/", view_func=TagsResource.as_view("TagsResource"))


@doc(tags=["tags"])
class TagResource(MethodResource):
    @doc(
        summary="Update tag translations",
        description="Update translations for a tag. Requires admin role."
    )
    @login_required
    def put(self, tag_name):
        if not current_user_role_is_at_least('admin'):
            raise InvalidPermissions("Admin role required")
            
        translations = request.get_json()
        tag = event_tags.update_tag_translations(tag_name, translations)
        return jsonify({
            "message": "Translations updated",
            "tag": tag.tag,
            "translations": tag.tag_translations
        })

    @doc(
        summary="Delete a tag",
        description="Delete a tag and all its associations. Requires admin role."
    )
    @login_required
    def delete(self, tag_name):
        if not current_user_role_is_at_least('admin'):
            raise InvalidPermissions("Admin role required")
            
        event_tags.delete_tag(tag_name)
        return jsonify({"message": "Tag deleted"})


event_tags_blueprint.add_url_rule(
    "/<string:tag_name>/",
    view_func=TagResource.as_view("TagResource")
)
