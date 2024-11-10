import json
from flask import Blueprint
from marshmallow import fields
from flask_apispec import doc
from flask_apispec import MethodResource
from flask_apispec import use_kwargs
from flask_apispec import marshal_with
import pmapi.event_artist.controllers as artists
from pmapi.hcaptcha.controllers import validate_hcaptcha
from pmapi.suggestions.controllers import add_suggested_edit
from .schemas import ArtistSchema, ArtistListSchema
import pmapi.event_artist.permissions as artist_permissions
from pmapi.common.controllers import paginated_view_args
from flask_login import login_required
from flask_login import current_user
from pmapi.user.controllers import action_as_system_user


artists_blueprint = Blueprint("artists", __name__)


@doc(tags=["artist"])
class ArtistResource(MethodResource):
    @doc(
        summary="Get artist info.",
        params={"id": {"description": "artist ID"}},
    )
    @marshal_with(ArtistSchema(), code=200)
    def get(self, **kwargs):
        return artists.get_artist_or_404(**kwargs)

    @doc(
        summary="Update artist info.",
        params={"id": {"description": "artist ID"}},
    )
    @use_kwargs(
        {
            "name": fields.Str(required=False, allow_none=True),
            "mbid": fields.Str(required=False, allow_none=True),
            "popularity": fields.Int(required=False, allow_none=True),
            "description": fields.Str(required=False, allow_none=True),
            "disambiguation": fields.Str(required=False, allow_none=True),
            "area": fields.Str(required=False, allow_none=True),
            "add_tags": fields.List(fields.Str(), required=False, allow_none=True),
            "remove_tags": fields.List(fields.Str(), required=False, allow_none=True),
            "add_urls": fields.List(fields.Dict(), required=False, allow_none=True),
            "remove_urls": fields.List(fields.Str(), required=False, allow_none=True),
            "media_items": fields.List(fields.Dict(), required=False, allow_none=True),
        },
        location="query"
    )
    @marshal_with(ArtistSchema(), code=200)
    @login_required
    @artist_permissions.update
    def put(self, id, **kwargs):
        return artists.update_artist(id, **kwargs)

    @doc(
        summary="Delete artist.",
        params={"id": {"description": "artist ID"}},
    )
    @login_required
    @artist_permissions.delete
    def delete(self, id, **kwargs):
        artists.delete_artist(id, **kwargs)
        return "", 204


artists_blueprint.add_url_rule(
    "/<id>", view_func=ArtistResource.as_view("ArtistResource")
)


@doc(tags=["dates", "suggest_edit"])
class ArtistSuggestResource(MethodResource):
    @doc(
        summary="Suggest deleting an artist.",
        params={"id": {"description": "event date ID"}},
    )
    @use_kwargs(
        {
            "message": fields.Str(required=False, allow_none=True),
            "hcaptcha_token": fields.Str(required=False, allow_none=True),
        }
    )
    def delete(self, id, **kwargs):
        # used by unpriviliged users to suggest updates
        token = kwargs.pop("hcaptcha_token", None)
        artist = artists.get_artist_or_404(id)
        if not current_user.is_authenticated:
            validate_hcaptcha(token)

        return add_suggested_edit(
            action="delete",
            artist=artist,
            creator_id=current_user.get_id(),
            object_type="Artist",
        )


    @doc(summary="Suggest an edit to an artist")
    @use_kwargs(
        {
            "name": fields.Str(required=False, allow_none=True),
            "mbid": fields.Str(required=False, allow_none=True),
            "popularity": fields.Int(required=False, allow_none=True),
            "description": fields.Str(required=False, allow_none=True),
            "disambiguation": fields.Str(required=False, allow_none=True),
            "area": fields.Str(required=False, allow_none=True),
            "add_tags": fields.List(fields.Str(), required=False, allow_none=True),
            "remove_tags": fields.List(fields.Str(), required=False, allow_none=True),
            "add_urls": fields.List(fields.Dict(), required=False, allow_none=True),
            "remove_urls": fields.List(fields.Str(), required=False, allow_none=True),
            "media_items": fields.List(fields.Dict(), required=False, allow_none=True),
        }
    )
    def put(self, id, **kwargs):
        # used by unpriviliged users to suggest updates
        token = kwargs.pop("hcaptcha_token", None)
        artist = artists.get_artist_or_404(id)
        if not current_user.is_authenticated:
            validate_hcaptcha(token)

        return add_suggested_edit(
            action="update",
            artist=artist,
            creator_id=current_user.get_id(),
            object_type="Artist",
            **kwargs
        )


artists_blueprint.add_url_rule(
    "/<id>/suggest",
    view_func=ArtistSuggestResource.as_view("ArtistSuggestResource"),
)


@doc(tags=["artist"])
class ArtistRefreshResource(MethodResource):
    @doc(
        summary="Refresh artist info from Musicbrainz and Last.fm.",
        params={"id": {"description": "artist ID"}},
    )
    @login_required
    @marshal_with(ArtistSchema(), code=200)
    @action_as_system_user
    def get(self, **kwargs):
        return artists.refresh_info(**kwargs)


artists_blueprint.add_url_rule(
    "/<id>/refresh", view_func=ArtistRefreshResource.as_view("ArtistRefreshResource")
)


@doc(tags=["artist"])
class ArtistsResource(MethodResource):
    @doc(
        summary="Get all artists",
        params={
            "query": {"description": "search query"},
        },
    )
    @use_kwargs(
        {
            "query": fields.String(required=False, allow_none=True),
            "date_min": fields.DateTime(required=False),
            "date_max": fields.DateTime(required=False),
            "radius": fields.Int(),
            "location": fields.Str(),
            "bounds": fields.Str(),
            **paginated_view_args(
                sort_options=["event_count", "created_at",
                              "name", "popularity", "id"]
            ),
        },
        location="query"
    )
    @marshal_with(ArtistListSchema(), code=200)
    def get(self, **kwargs):
        # get json from query string
        if kwargs.get("location"):
            kwargs["location"] = json.loads(kwargs["location"])
        if kwargs.get("bounds"):
            kwargs["bounds"] = json.loads(kwargs["bounds"])

        return artists.get_artists(**kwargs)


artists_blueprint.add_url_rule(
    "/", view_func=ArtistsResource.as_view("ArtistsResource")
)
