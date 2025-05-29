from flask import Blueprint

from marshmallow import fields
from flask_apispec import doc
from flask_apispec import marshal_with
from flask_apispec import MethodResource
from flask_apispec import use_kwargs
from flask_login import login_required
from pmapi.common.controllers import paginated_view_args
from .schemas import UrlSummarySortableSchema, CountryVisitorSummarySchema
from . import permissions as metrics_permissions
import pmapi.metrics.controllers as metrics

from pmapi.extensions import tracker


per_page = 20

metrics_blueprint = Blueprint("metrics", __name__)


@doc(tags=["metrics"])
class UrlMetricResource(MethodResource):
    @doc(
        summary="Get URL Metrics",
    )
    @use_kwargs(
        {
            "country": fields.String(required=False),
            "start_time": fields.DateTime(),
            "end_time": fields.DateTime(),
            "limit": fields.Integer(required=False),
            **paginated_view_args(sort_options=['views', 'unique_views', 'avg_speed', 'error_rate', 'url']),
        },         
        location="query"
    )
    @marshal_with(UrlSummarySortableSchema(), code=200)
   # @login_required
   # @metrics_permissions.view_metrics
    def get(self, **kwargs):
        return metrics.get_url_summary_sortable(**kwargs)


metrics_blueprint.add_url_rule(
    "/urls", view_func=UrlMetricResource.as_view("UrlMetricResource")
)

@doc(tags=["metrics"])
class CountryMetricResource(MethodResource):
    @doc(
        summary="Get Country Metrics",
    )
    @use_kwargs(
        {
            "start_time": fields.DateTime(),
            "end_time": fields.DateTime(),
            **paginated_view_args(sort_options=['views']),
        },         
        location="query"
    )
    @marshal_with(CountryVisitorSummarySchema(), code=200)
    def get(self, **kwargs):
        return metrics.get_country_visitor_summary(**kwargs)

metrics_blueprint.add_url_rule(
    "/countries", view_func=CountryMetricResource.as_view("CountryMetricResource")
)