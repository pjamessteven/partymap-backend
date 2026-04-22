import pytest
from flask import url_for


# ---------------------------------------------------------------------------
# Suggestion management endpoints
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="TODO")
def test_list_suggestions_as_staff(staff_user, complete_event_factory, anon_user, mock_hcaptcha):
    """GET /suggestions/ as staff should list all suggested edits."""
    pass


@pytest.mark.skip(reason="TODO")
def test_list_suggestions_filtered_by_status(staff_user, complete_event_factory, anon_user, mock_hcaptcha):
    """GET /suggestions/?status=pending should filter suggestions by status."""
    pass


@pytest.mark.skip(reason="TODO")
def test_list_suggestions_event_filter(staff_user, complete_event_factory, anon_user, mock_hcaptcha):
    """GET /suggestions/?event_id=... should filter to suggestions for a specific event."""
    pass


@pytest.mark.skip(reason="TODO")
def test_update_suggestion_status_as_staff(staff_user, complete_event_factory, anon_user, mock_hcaptcha):
    """PUT /suggestions/<id>/ as staff should approve/reject a suggestion."""
    pass


@pytest.mark.skip(reason="TODO")
def test_delete_suggestion_as_staff(staff_user, complete_event_factory, anon_user, mock_hcaptcha):
    """DELETE /suggestions/<id>/ as staff should delete a suggestion."""
    pass


@pytest.mark.skip(reason="TODO")
def test_list_suggestions_unauthorized(regular_user):
    """GET /suggestions/ as regular user should return 403."""
    pass


@pytest.mark.skip(reason="TODO")
def test_update_suggestion_unauthorized(regular_user):
    """PUT /suggestions/<id>/ as regular user should return 403."""
    pass


# ---------------------------------------------------------------------------
# Suggestion creation via event / event_date / artist endpoints
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="TODO")
def test_suggest_event_edit_as_anon(complete_event_factory, anon_user, mock_hcaptcha):
    """PUT /event/<id>/suggest as anon should create a suggested edit."""
    pass


@pytest.mark.skip(reason="TODO")
def test_suggest_event_delete_as_anon(complete_event_factory, anon_user, mock_hcaptcha):
    """DELETE /event/<id>/suggest as anon should create a suggested deletion."""
    pass


@pytest.mark.skip(reason="TODO")
def test_suggest_event_date_add_as_anon(complete_event_factory, anon_user, mock_hcaptcha):
    """POST /date/event/<id>/suggest as anon should create a suggested date addition."""
    pass


@pytest.mark.skip(reason="TODO")
def test_suggest_event_date_edit_as_anon(complete_event_factory, anon_user, mock_hcaptcha):
    """PUT /date/<id>/suggest as anon should create a suggested date edit."""
    pass


@pytest.mark.skip(reason="TODO")
def test_suggest_event_date_delete_as_anon(complete_event_factory, anon_user, mock_hcaptcha):
    """DELETE /date/<id>/suggest as anon should create a suggested date deletion."""
    pass


@pytest.mark.skip(reason="TODO")
def test_suggest_artist_edit_as_anon(anon_user, mock_hcaptcha):
    """PUT /artist/<id>/suggest as anon should create a suggested artist edit."""
    pass


@pytest.mark.skip(reason="TODO")
def test_suggest_artist_delete_as_anon(anon_user, mock_hcaptcha):
    """DELETE /artist/<id>/suggest as anon should create a suggested artist deletion."""
    pass
