from flask import Blueprint

from marshmallow import fields
from flask_apispec import doc
from flask_apispec import MethodResource
from flask_apispec import use_kwargs
from flask_apispec import marshal_with
import pmapi.event_artist.controllers as artists
from .schemas import ArtistSchema, ArtistListSchema
from pmapi.common.controllers import paginated_view_args
from flask_login import login_required


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


artists_blueprint.add_url_rule(
    "/<id>", view_func=ArtistResource.as_view("ArtistResource")
)


@doc(tags=["artist"])
class ArtistRefreshResource(MethodResource):
    @doc(
        summary="Refresh artist info from Musicbrainz and Last.fm.",
        params={"id": {"description": "artist ID"}},
    )
    @login_required
    @marshal_with(ArtistSchema(), code=200)
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
            **paginated_view_args(sort_options=["event_count", "created_at"]),
        },
        location="query",
    )
    @marshal_with(ArtistListSchema(), code=200)
    def get(self, **kwargs):
        return artists.get_artists(**kwargs)


artists_blueprint.add_url_rule(
    "/", view_func=ArtistsResource.as_view("ArtistsResource")
)
