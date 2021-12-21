from flask import Blueprint, jsonify
from marshmallow import fields
from flask_apispec import doc
from flask_apispec import marshal_with
from flask_apispec import MethodResource
from flask_apispec import use_kwargs
from flask_login import login_required
from flask_login import current_user

from . import controllers as suggestions
import pmapi.activity.controllers as activities
from . import permissions as suggestions_permissions

from pmapi.exceptions import InvalidUsage
from pmapi.common.controllers import paginated_view_args

from .schemas import (
    SuggestedEditSchema,
    SuggestedEditListSchema,
)

suggestions_blueprint = Blueprint("suggestions", __name__)

# Activity = activity_plugin.activity_cls


@doc(tags=["events"])
class SuggestedEditsResource(MethodResource):
    @doc(
        summary="Get a list of suggested edits that are in the db.",
        description="""Returns a list of event dates that are in the db. \n
        ### Usage:  \n
        Start and end date format must be in ISO-8601 format.
        eg: 2020-05-23T05:00:00",
        """,
    )
    @use_kwargs(
        {
            "event_id": fields.String(required=False),
            "status": fields.String(required=False, allow_none=True),
            **paginated_view_args(sort_options=["created_at"]),
        },
        location="query",
    )
    @suggestions_permissions.get
    @marshal_with(SuggestedEditListSchema(), code=200)
    def get(self, **kwargs):
        return suggestions.get_suggested_edits(**kwargs)


suggestions_blueprint.add_url_rule(
    "/", view_func=SuggestedEditsResource.as_view("SuggestedEditsResource")
)


@doc(tags=["events"])
class SuggestedEditResource(MethodResource):
    @doc(summary="Update a suggested edit")
    @login_required
    @suggestions_permissions.update
    @use_kwargs(
        {
            "status": fields.String(required=True, allow_none=False),
        },
    )
    @marshal_with(SuggestedEditSchema(), code=200)
    def put(self, suggested_edit_id, **kwargs):
        print("test!", kwargs)
        return suggestions.update_suggested_edit(suggested_edit_id, **kwargs)

    @doc(summary="Delete an suggested edit")
    @login_required
    @suggestions_permissions.delete
    def delete(self, suggested_edit_id):
        suggestions.delete_suggested_edit(suggested_edit_id)
        return "", 204


suggestions_blueprint.add_url_rule(
    "/<suggested_edit_id>/",
    view_func=SuggestedEditResource.as_view("SuggestedEditResource"),
)
