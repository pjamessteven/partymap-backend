from flask import url_for


def test_create_report_as_auth(regular_user, complete_event_factory):
    """POST /report/ as authenticated user should create a report."""
    event = complete_event_factory(creator=regular_user)
    payload = {
        "event_id": event.id,
        "message": "This event has inappropriate content",
    }
    rv = regular_user.client.post(url_for("reports_blueprint.ReportsResource"), json=payload)
    # create_report returns None, so response is empty but status should be 200
    assert rv.status_code == 200


def test_create_report_for_event_review(regular_user, complete_event_factory):
    """POST /report/ targeting an event_review should succeed."""
    event = complete_event_factory(creator=regular_user)
    # First add a review
    review_rv = regular_user.client.post(
        url_for("event_review.AddEventReviewResource", event_id=event.id),
        json={"text": "Test review"},
    )
    assert review_rv.status_code == 200
    review_id = review_rv.json["id"]

    payload = {
        "event_review_id": str(review_id),
        "event_id": event.id,
        "message": "This review is spam",
    }
    rv = regular_user.client.post(url_for("reports_blueprint.ReportsResource"), json=payload)
    assert rv.status_code == 200


def test_list_reports_as_staff(staff_user, regular_user, complete_event_factory):
    """GET /report/ as staff should return all reports."""
    event = complete_event_factory(creator=regular_user)
    # Create a report first
    payload = {"event_id": event.id, "message": "Test report"}
    regular_user.client.post(url_for("reports_blueprint.ReportsResource"), json=payload)

    rv = staff_user.client.get(url_for("reports_blueprint.ReportsResource"))
    assert rv.status_code == 200
    assert "items" in rv.json


def test_list_reports_as_regular_user_forbidden(regular_user):
    """GET /report/ as regular user should return 403."""
    rv = regular_user.client.get(url_for("reports_blueprint.ReportsResource"))
    assert rv.status_code == 403


def test_update_report_as_staff(staff_user, regular_user, complete_event_factory, db):
    """PUT /report/<id> as staff should update report status."""
    from pmapi.report.model import Report
    event = complete_event_factory(creator=regular_user)
    report = Report(
        event_id=event.id,
        message="Test report",
        creator_id=regular_user.id,
        email=regular_user.email,
        open=True,
    )
    db.session.add(report)
    db.session.commit()

    rv = staff_user.client.put(
        url_for("reports_blueprint.ReportResource", id=report.id),
        json={"open": False},
    )
    assert rv.status_code == 200
    assert rv.json["open"] is False


def test_delete_report_as_staff(staff_user, regular_user, complete_event_factory, db):
    """DELETE /report/<id> as staff should delete the report."""
    from pmapi.report.model import Report
    event = complete_event_factory(creator=regular_user)
    report = Report(
        event_id=event.id,
        message="Test report",
        creator_id=regular_user.id,
        email=regular_user.email,
        open=True,
    )
    db.session.add(report)
    db.session.commit()

    rv = staff_user.client.delete(url_for("reports_blueprint.ReportResource", id=report.id))
    # delete_report returns None which becomes 200 with null body
    assert rv.status_code == 200


def test_update_report_unauthorized(regular_user, complete_event_factory, db):
    """PUT /report/<id> as regular user should return 403."""
    from pmapi.report.model import Report
    event = complete_event_factory(creator=regular_user)
    report = Report(
        event_id=event.id,
        message="Test report",
        creator_id=regular_user.id,
        email=regular_user.email,
        open=True,
    )
    db.session.add(report)
    db.session.commit()

    rv = regular_user.client.put(
        url_for("reports_blueprint.ReportResource", id=report.id),
        json={"open": False},
    )
    assert rv.status_code == 403
