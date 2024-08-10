from flask import Blueprint

from marshmallow import fields
from flask_apispec import doc
from flask_apispec import marshal_with
from flask_apispec import MethodResource
from flask_apispec import use_kwargs
from flask_login import login_required
from .schemas import MediaItemSchema
from . import permissions as media_item_permissions
import pmapi.media_item.controllers as media_items

per_page = 20

media_blueprint = Blueprint("media", __name__)


@doc(tags=["albums"])
class MediaItemResource(MethodResource):
    @doc(
        summary="Update an item.",
        description="""Update a media items description or position.
        Must be event creator or admin.""",
        params={"id": {"description": "event item ID"}},
    )
    @use_kwargs({"position": fields.Int(), "caption": fields.String()})
    @marshal_with(MediaItemSchema(), code=200)
    @login_required
    @media_item_permissions.update_media_item
    def put(self, id, **kwargs):
        return media_items.update_item(id, **kwargs)

    @doc(
        summary="Delete a media item.",
        description="""Delete a media item. Must be event creator or admin.""",
        params={"id": {"description": "event item ID"}},
    )
    @login_required
    @media_item_permissions.delete_media_item
    def delete(self, id):
        return media_items.delete_item_by_id(id)


media_blueprint.add_url_rule(
    "/<id>", view_func=MediaItemResource.as_view("MediaItemResource")
)
