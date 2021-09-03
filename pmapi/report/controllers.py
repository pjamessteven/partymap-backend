import pmapi.exceptions as exc
from pmapi.common.controllers import paginated_results
from pmapi.mail.controllers import (
    send_report_notification_email,
)
from pmapi.extensions import db
import pmapi.event.controllers as events

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
    message = kwargs.pop("message", None)
    event_id = kwargs.pop("event_id", None)
    event = events.get_event_or_404(event_id)

    report = Report(creator=creator, message=message, event=event, open=True)
    db.session.add(report)
    db.session.commit()
    send_report_notification_email(report.id, message, creator)


def delete_report(id):
    report = get_report_or_404(id)
    db.session.delete(report)
    db.session.commit()
