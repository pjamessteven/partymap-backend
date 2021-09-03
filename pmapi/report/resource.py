from flask import Blueprint
from flask_login import current_user

from marshmallow import fields
from flask_apispec import doc
from flask_apispec import marshal_with
from flask_apispec import MethodResource
from flask_apispec import use_kwargs
from flask_login import login_required
from .schemas import ReportSchema
from . import permissions as report_permissions
import pmapi.report.controllers as reports


reports_blueprint = Blueprint("reports_blueprint", __name__)


@doc(tags=["reports"])
class ReportsResource(MethodResource):
    @doc(
        summary="Create a report.",
        description="""Create a report. Must be signed in.""",
    )
    @use_kwargs({"event_id": fields.UUID(), "message": fields.String()})
    @marshal_with(ReportSchema(), code=200)
    @login_required
    def post(self, **kwargs):
        return reports.create_report(**kwargs, creator=current_user)


reports_blueprint.add_url_rule(
    "/", view_func=ReportsResource.as_view("ReportsResource")
)


@doc(tags=["reports"])
class ReportResource(MethodResource):
    @doc(
        summary="Delete a report.",
        description="""Delete a report. Must be admin.""",
        params={"id": {"description": "report ID"}},
    )
    @login_required
    @report_permissions.delete_report
    def delete(self, id):
        return reports.delete_report(id)


reports_blueprint.add_url_rule(
    "/<id>", view_func=ReportResource.as_view("ReportResource")
)
