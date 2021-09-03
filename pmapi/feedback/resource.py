from flask import Blueprint

from marshmallow import fields
from flask_apispec import doc
from flask_apispec import MethodResource
from flask_apispec import use_kwargs
import pmapi.feedback.controllers as feedback


feedback_blueprint = Blueprint("feedback_blueprint", __name__)


@doc(tags=["reports"])
class FeedbackResource(MethodResource):
    @doc(
        summary="Create feedback.",
    )
    @use_kwargs(
        {
            "message": fields.String(required=True),
            "contact_email": fields.String(required=False, allow_none=True),
        }
    )
    def post(self, **kwargs):
        return feedback.create_feedback(**kwargs)


feedback_blueprint.add_url_rule(
    "/", view_func=FeedbackResource.as_view("FeedbackResource")
)
