import pytest
from flask import url_for


# ---------------------------------------------------------------------------
# Review / contribution endpoints
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="TODO")
def test_add_review_to_event(regular_user, complete_event_factory):
    """POST /contribution/event/<event_id>/ should add a review."""
    pass


@pytest.mark.skip(reason="TODO")
def test_add_review_with_parent(regular_user, complete_event_factory):
    """POST /contribution/event/<event_id>/ with parent_id should create a reply."""
    pass


@pytest.mark.skip(reason="TODO")
def test_add_review_with_media_items(regular_user, complete_event_factory, mock_image_download):
    """POST /contribution/event/<event_id>/ with media_items should attach images."""
    pass


@pytest.mark.skip(reason="TODO")
def test_get_review_with_children(anon_user, regular_user, complete_event_factory):
    """GET /contribution/<review_id> should return review and direct children."""
    pass


@pytest.mark.skip(reason="TODO")
def test_delete_own_review(regular_user, complete_event_factory):
    """DELETE /contribution/<review_id> as creator should succeed."""
    pass


@pytest.mark.skip(reason="TODO")
def test_delete_review_as_staff(regular_user, staff_user, complete_event_factory):
    """DELETE /contribution/<review_id> as staff should succeed."""
    pass


@pytest.mark.skip(reason="TODO")
def test_delete_review_unauthorized(regular_user_factory, complete_event_factory):
    """DELETE /contribution/<review_id> as non-creator/non-staff should return 403."""
    pass
