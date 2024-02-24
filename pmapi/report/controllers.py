import pmapi.exceptions as exc
from pmapi.common.controllers import paginated_results
from pmapi.mail.controllers import (
    send_report_notification_email,
)
from pmapi.extensions import db
import pmapi.exceptions as exc
from pmapi import validate
import pmapi.event.controllers as events
import pmapi.media_item.controllers as media_items
import pmapi.user.controllers as users
from pmapi.hcaptcha.controllers import validate_hcaptcha

from flask_login import current_user

from .model import Report
from pmapi.config import BaseConfig


def get_all_reports(**kwargs):
    query = db.session.query(Report)

    if "open" in kwargs:
        query = query.filter(Report.open == kwargs.pop("open"))

    return paginated_results(Report, query=query, **kwargs)


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
    creator_id = current_user.get_id()
    user = users.get_user_or_404(
        creator_id
    )  # should get anonymous user if not authenticated
    message = kwargs.pop("message", None)
    email = kwargs.pop("email", None)
    event_id = kwargs.pop("event_id", None)
    media_item_id = kwargs.pop("media_item_id", None)
    event_contribution_id = kwargs.pop("event_contribution_id", None)
    token = kwargs.pop("hcaptcha_token", None)

    event = events.get_event(event_id)

    contribution = None

    if event_contribution_id:
        contribution = event_contributions.get_contribution(
            event_contribution_id)

    if media_item_id:
        media_item = media_items.get_media_item_or_404(
            media_item_id)

    if not current_user.is_authenticated and email is None:
        raise exc.InvalidAPIRequest("Email is required if not logged in")
    elif not current_user.is_authenticated:
        validate.email(email)
        if not validate_hcaptcha(token):
            raise exc.InvalidAPIRequest("HCaptcha not valid")
        # hcaptcha required if not logged in
    else:
        # user is not anonymous
        email = user.email

    report = Report(
        creator_id=creator_id, message=message, media_item=media_item, email=email, event=event, event_contribution=contribution, open=True
    )
    db.session.add(report)
    db.session.commit()

    send_report_notification_email(report.id, message, email, user.username)


def delete_report(id):
    report = get_report_or_404(id)
    db.session.delete(report)
    db.session.commit()


def update_report(id, **kwargs):
    report = get_report_or_404(id)
    if "open" in kwargs:
        report.open = kwargs.pop("open")
    db.session.commit()
    return report
