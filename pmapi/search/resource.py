from flask import Blueprint
from marshmallow import fields
from flask_apispec import doc
from flask_apispec import marshal_with
from flask_apispec import MethodResource
from flask_apispec import use_kwargs

from . import controllers as search

from .schemas import (
    SearchSchema,
)

search_blueprint = Blueprint("search", __name__)


@doc(tags=["search"])
class SearchResource(MethodResource):
    @doc(
        summary="Search db.",
        description="""Search main attributes of database. Used for search suggestions.
        """,
    )
    @use_kwargs(
        {
            "query": fields.String(required=False, allow_none=True),
        },
        location="query"
    )
    @marshal_with(SearchSchema(), code=200)
    def get(self, **kwargs):
        return search.search(kwargs.pop("query"))


search_blueprint.add_url_rule(
    "/", view_func=SearchResource.as_view("SearchResource"))
