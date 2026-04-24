from flask import url_for


# ---------------------------------------------------------------------------
# Feedback endpoints
# ---------------------------------------------------------------------------


def test_create_feedback_anon(anon_user):
    """POST /api/feedback/ as anonymous should create feedback."""
    rv = anon_user.client.post(
        url_for("feedback_blueprint.FeedbackResource"),
        json={"message": "This app is great!"},
    )
    assert rv.status_code == 200


def test_create_feedback_with_email(anon_user):
    """POST /api/feedback/ with contact_email should be accepted."""
    rv = anon_user.client.post(
        url_for("feedback_blueprint.FeedbackResource"),
        json={"message": "Found a bug", "contact_email": "user@example.com"},
    )
    assert rv.status_code == 200


def test_create_feedback_authenticated(regular_user):
    """POST /api/feedback/ as logged-in user should create feedback."""
    rv = regular_user.client.post(
        url_for("feedback_blueprint.FeedbackResource"),
        json={"message": "Love the new features!"},
    )
    assert rv.status_code == 200


def test_create_feedback_missing_message(anon_user):
    """POST /api/feedback/ without message should return 400."""
    rv = anon_user.client.post(
        url_for("feedback_blueprint.FeedbackResource"),
        json={},
    )
    assert rv.status_code == 400
