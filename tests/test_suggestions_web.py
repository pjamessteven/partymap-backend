from flask import url_for


import pytest

def test_list_suggestions_as_admin(admin_user, complete_event_factory, anon_user, mock_hcaptcha):
    """GET /suggestions/ as admin should list all suggested edits."""
    event = complete_event_factory()
    # Create a suggestion as anon
    anon_user.client.put(
        url_for("events.EventSuggestEditResource", event_id=event.id),
        json={"name": "Suggested name", "message": "Please update", "hcaptcha_token": "dummy"},
    )

    rv = admin_user.client.get(url_for("suggestions.SuggestedEditsResource"))
    assert rv.status_code == 200
    assert "items" in rv.json


def test_list_suggestions_filtered_by_status(admin_user, complete_event_factory, anon_user, mock_hcaptcha):
    """GET /suggestions/?status=pending should filter suggestions by status."""
    event = complete_event_factory()
    anon_user.client.put(
        url_for("events.EventSuggestEditResource", event_id=event.id),
        json={"name": "Suggested name", "message": "Please update", "hcaptcha_token": "dummy"},
    )

    rv = admin_user.client.get(url_for("suggestions.SuggestedEditsResource", status="pending"))
    assert rv.status_code == 200
    assert "items" in rv.json


def test_list_suggestions_event_filter(admin_user, complete_event_factory, anon_user, mock_hcaptcha):
    """GET /suggestions/?event_id=... should filter to suggestions for a specific event."""
    event = complete_event_factory()
    anon_user.client.put(
        url_for("events.EventSuggestEditResource", event_id=event.id),
        json={"name": "Suggested name", "message": "Please update", "hcaptcha_token": "dummy"},
    )

    rv = admin_user.client.get(url_for("suggestions.SuggestedEditsResource", event_id=event.id))
    assert rv.status_code == 200


def test_update_suggestion_status_as_admin(admin_user, complete_event_factory, anon_user, mock_hcaptcha):
    """PUT /suggestions/<id>/ as admin should approve/reject a suggestion."""
    event = complete_event_factory()
    anon_user.client.put(
        url_for("events.EventSuggestEditResource", event_id=event.id),
        json={"name": "Suggested name", "message": "Please update", "hcaptcha_token": "dummy"},
    )

    # Get the suggestion ID
    list_rv = admin_user.client.get(url_for("suggestions.SuggestedEditsResource"))
    suggestion_id = list_rv.json["items"][0]["id"]

    rv = admin_user.client.put(
        url_for("suggestions.SuggestedEditResource", suggested_edit_id=suggestion_id),
        json={"status": "hidden"},
    )
    assert rv.status_code == 200
    assert rv.json["status"] == "hidden"


def test_delete_suggestion_as_admin(admin_user, complete_event_factory, anon_user, mock_hcaptcha):
    """DELETE /suggestions/<id>/ as admin should delete a suggestion."""
    event = complete_event_factory()
    anon_user.client.put(
        url_for("events.EventSuggestEditResource", event_id=event.id),
        json={"name": "Suggested name", "message": "Please update", "hcaptcha_token": "dummy"},
    )

    list_rv = admin_user.client.get(url_for("suggestions.SuggestedEditsResource"))
    suggestion_id = list_rv.json["items"][0]["id"]

    rv = admin_user.client.delete(
        url_for("suggestions.SuggestedEditResource", suggested_edit_id=suggestion_id)
    )
    assert rv.status_code == 204


def test_list_suggestions_unauthorized(regular_user):
    """GET /suggestions/ as regular user should return 403."""
    rv = regular_user.client.get(url_for("suggestions.SuggestedEditsResource"))
    assert rv.status_code == 403


def test_update_suggestion_unauthorized(regular_user):
    """PUT /suggestions/<id>/ as regular user should return 403."""
    rv = regular_user.client.put(
        url_for("suggestions.SuggestedEditResource", suggested_edit_id=1),
        json={"status": "approved"},
    )
    assert rv.status_code == 403


# ---------------------------------------------------------------------------
# Suggestion creation via event / event_date / artist endpoints
# ---------------------------------------------------------------------------


def test_suggest_event_edit_as_anon(complete_event_factory, anon_user, mock_hcaptcha):
    """PUT /event/<id>/suggest as anon should create a suggested edit."""
    event = complete_event_factory()
    rv = anon_user.client.put(
        url_for("events.EventSuggestEditResource", event_id=event.id),
        json={"name": "Suggested name", "message": "Please update", "hcaptcha_token": "dummy"},
    )
    assert rv.status_code == 200


def test_suggest_event_delete_as_anon(complete_event_factory, anon_user, mock_hcaptcha):
    """DELETE /event/<id>/suggest as anon should create a suggested deletion."""
    event = complete_event_factory()
    rv = anon_user.client.delete(
        url_for("events.EventSuggestEditResource", event_id=event.id),
        json={"message": "Please delete this event", "hcaptcha_token": "dummy"},
    )
    assert rv.status_code == 200


def test_suggest_event_date_edit_as_anon(complete_event_factory, anon_user, mock_hcaptcha):
    """PUT /date/<id>/suggest as anon should create a suggested date edit."""
    event = complete_event_factory()
    event_date = event.event_dates[0]
    rv = anon_user.client.put(
        url_for("dates.EventDateSuggestResource", id=event_date.id),
        json={"description": "Suggested description", "message": "Please update", "hcaptcha_token": "dummy"},
    )
    assert rv.status_code == 200


def test_suggest_event_date_delete_as_anon(complete_event_factory, anon_user, mock_hcaptcha):
    """DELETE /date/<id>/suggest as anon should create a suggested date deletion."""
    event = complete_event_factory()
    event_date = event.event_dates[0]
    rv = anon_user.client.delete(
        url_for("dates.EventDateSuggestResource", id=event_date.id),
        json={"message": "Please delete this date", "hcaptcha_token": "dummy"},
    )
    assert rv.status_code == 200
