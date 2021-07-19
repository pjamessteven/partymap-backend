import pmapi.exceptions as exc
from pmapi.common.controllers import paginated_results
from pmapi.mail.controllers import (
    send_report_notification_email,
)
from pmapi.extensions import db

from .model import Report


def get_all_reports(**kwargs):
    return paginated_results(Report, **kwargs)


def get_report(report_id):
    return Report.query.get(report_id)


def get_report_or_404(report_id):
    """Return a report or raise 404 exception"""
    report = get_report(report_id)
    if not report:
        msg = "No such report with id {}".format(report_id)
        raise exc.RecordNotFound(msg)

    return report


def create_report(**kwargs):
    creator = kwargs.pop("creator", None)
    description = kwargs.pop("description", None)

    contribution_id = kwargs.pop("contribution_id", None)
    event_id = kwargs.pop("event_id", None)
    media_item_id = kwargs.pop("media_item_id", None)

    report = Report(creator, description, contribution_id, event_id, media_item_id)
    db.session.add(report)
    db.session.commit()
    send_report_notification_email(report.id, description, creator)


def delete_report(id):
    report = get_report_or_404(id)
    db.session.delete(report)
    db.session.commit()
