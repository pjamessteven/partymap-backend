import pytest
from flask import url_for


# ---------------------------------------------------------------------------
# Feedback endpoint
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="TODO")
def test_submit_feedback(anon_user):
    """POST /feedback/ with a message should create feedback."""
    pass


@pytest.mark.skip(reason="TODO")
def test_submit_feedback_with_contact_email(anon_user):
    """POST /feedback/ with message and contact_email should store both."""
    pass
