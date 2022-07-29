from flask import Blueprint
from flask_login import current_user

from marshmallow import fields
from flask_apispec import doc
from flask_apispec import marshal_with
from flask_apispec import MethodResource
from flask_apispec import use_kwargs
from flask_login import login_required
from .schemas import ReportSchema, ReportListSchema
from . import permissions as report_permissions
import pmapi.report.controllers as reports
from pmapi.common.controllers import paginated_view_args


reports_blueprint = Blueprint("reports_blueprint", __name__)


@doc(tags=["reports"])
class ReportsResource(MethodResource):
    @doc(
        summary="Create a report.",
        description="""Create a report.""",
    )
    @use_kwargs(
        {
            "event_id": fields.Integer(),
            "message": fields.String(),
            "email": fields.String(required=False, allow_none=True),
            "hcaptcha_token": fields.Str(required=False, allow_none=True),
        }
    )
    @marshal_with(ReportSchema(), code=200)
    def post(self, **kwargs):
        return reports.create_report(**kwargs)

    @doc(
        summary="Get reports.",
        description="""Get all reports. Must be signed in.""",
    )
    @use_kwargs(
        {
            "open": fields.Boolean(),
            **paginated_view_args(sort_options=["created_at"]),
        },
    )
    @login_required
    @report_permissions.get_reports
    @marshal_with(ReportListSchema(), code=200)
    def get(self, **kwargs):
        return reports.get_all_reports(**kwargs)


reports_blueprint.add_url_rule(
    "/", view_func=ReportsResource.as_view("ReportsResource")
)


@doc(tags=["reports"])
class ReportResource(MethodResource):
    @doc(
        summary="Delete a report.",
        description="""Delete a report. Must be staff.""",
        params={"id": {"description": "report ID"}},
    )
    @login_required
    @report_permissions.delete_report
    def delete(self, id):
        return reports.delete_report(id)

    @doc(
        summary="Update a report.",
        description="""Update a report. Must be staff.""",
        params={"id": {"description": "report ID"}},
    )
    @use_kwargs(
        {
            "open": fields.Boolean(),
        }
    )
    @login_required
    @report_permissions.update_report
    @marshal_with(ReportSchema(), code=200)
    def put(self, id, **kwargs):
        return reports.update_report(id, **kwargs)


reports_blueprint.add_url_rule(
    "/<id>", view_func=ReportResource.as_view("ReportResource")
)
