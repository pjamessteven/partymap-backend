import pytest
from flask import url_for


# ---------------------------------------------------------------------------
# Report creation
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="TODO")
def test_create_report_as_anon(anon_user, complete_event_factory, mock_hcaptcha):
    """POST /report/ as anon should create a report."""
    pass


@pytest.mark.skip(reason="TODO")
def test_create_report_as_auth(regular_user, complete_event_factory):
    """POST /report/ as authenticated user should create a report."""
    pass


@pytest.mark.skip(reason="TODO")
def test_create_report_for_event_review(anon_user, regular_user, complete_event_factory, mock_hcaptcha):
    """POST /report/ targeting an event_review should succeed."""
    pass


@pytest.mark.skip(reason="TODO")
def test_create_report_for_media_item(anon_user, complete_event_factory, mock_hcaptcha):
    """POST /report/ targeting a media_item should succeed."""
    pass


# ---------------------------------------------------------------------------
# Report listing / management (staff only)
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="TODO")
def test_list_reports_as_staff(staff_user):
    """GET /report/ as staff should return all reports."""
    pass


@pytest.mark.skip(reason="TODO")
def test_list_reports_as_regular_user_forbidden(regular_user):
    """GET /report/ as regular user should return 403."""
    pass


@pytest.mark.skip(reason="TODO")
def test_update_report_as_staff(staff_user):
    """PUT /report/<id> as staff should update report status."""
    pass


@pytest.mark.skip(reason="TODO")
def test_delete_report_as_staff(staff_user):
    """DELETE /report/<id> as staff should delete the report."""
    pass


@pytest.mark.skip(reason="TODO")
def test_update_report_unauthorized(regular_user):
    """PUT /report/<id> as regular user should return 403."""
    pass
