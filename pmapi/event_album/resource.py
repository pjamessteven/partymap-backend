from flask import Blueprint

from marshmallow import fields
from flask_apispec import doc
from flask_apispec import marshal_with
from flask_apispec import MethodResource
from flask_apispec import use_kwargs
from flask_login import login_required
from .schemas import EventAlbumSchema, AlbumItemSchema
from . import permissions as event_album_permissions
import pmapi.event_album.controllers as event_albums

per_page = 20

event_albums_blueprint = Blueprint("albums", __name__)


@doc(tags=["albums"])
class AlbumResource(MethodResource):
    @doc(
        summary="Get an event album.",
        description="""Returns an event date \n
        """,
        params={"id": {"description": "event album ID"}},
    )
    @marshal_with(EventAlbumSchema(), code=200)
    def get(self, id):
        return event_albums.get_event_album_or_404(id)

    @doc(
        summary="Delete an event album.",
        description="""Delete an event album. Must be event creator or admin.""",
        params={"id": {"description": "event date ID"}},
    )
    @login_required
    @event_album_permissions.delete_album
    def delete(self, id):
        album = event_albums.get_event_or_404(id)
        event_albums.delete_event_album(album)
        return "", 204

    @doc(
        summary="Update an event album.",
        description="""Add images to an event album. Must be event creator or admin.""",
        params={"id": {"description": "event date ID"}},
    )
    @use_kwargs(
        {
            "items": fields.List(fields.Dict(), required=False, allow_none=True),
            "caption": fields.String(),
        }
    )
    @marshal_with(EventAlbumSchema(), code=200)
    @login_required
    @event_album_permissions.update_album
    def put(self, id, **kwargs):
        print(kwargs)
        album = event_albums.get_event_album_or_404(id)
        return event_albums.add_items_to_album(album=album, **kwargs)


event_albums_blueprint.add_url_rule(
    "/<id>", view_func=AlbumResource.as_view("AlbumResource")
)


@doc(tags=["albums"])
class AlbumItemResource(MethodResource):
    @doc(
        summary="Update an item.",
        description="""Update an item albums description or position.
        Must be event creator or admin.""",
        params={"id": {"description": "event item ID"}},
    )
    @use_kwargs({"position": fields.Int(), "caption": fields.String()})
    @marshal_with(AlbumItemSchema(), code=200)
    @login_required
    @event_album_permissions.update_album_item
    def put(self, id, **kwargs):
        return event_albums.update_item(id, **kwargs)

    @doc(
        summary="Delete an album item.",
        description="""Delete an album item. Must be event creator or admin.""",
        params={"id": {"description": "event item ID"}},
    )
    @login_required
    @event_album_permissions.delete_album_item
    def delete(self, id):
        return event_albums.delete_item(id)


event_albums_blueprint.add_url_rule(
    "/item/<id>", view_func=AlbumItemResource.as_view("AlbumItemResource")
)
