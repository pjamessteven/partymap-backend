import pytest
from flask import url_for


# ---------------------------------------------------------------------------
# Media item endpoint tests
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="TODO")
def test_update_media_item_caption(regular_user, complete_event_factory):
    """PUT /media/<id> with caption should update the media item caption."""
    pass


@pytest.mark.skip(reason="TODO")
def test_update_media_item_position(regular_user, complete_event_factory):
    """PUT /media/<id> with position should reorder the media item."""
    pass


@pytest.mark.skip(reason="TODO")
def test_delete_media_item_as_creator(regular_user, complete_event_factory):
    """DELETE /media/<id> as event creator should succeed."""
    pass


@pytest.mark.skip(reason="TODO")
def test_delete_media_item_as_staff(regular_user, staff_user, complete_event_factory):
    """DELETE /media/<id> as staff should succeed."""
    pass


@pytest.mark.skip(reason="TODO")
def test_delete_media_item_unauthorized(regular_user_factory, complete_event_factory):
    """DELETE /media/<id> as non-creator/non-staff should return 403."""
    pass


# ---------------------------------------------------------------------------
# Logo upload via event creation
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="TODO")
def test_create_event_logo_as_url(regular_user, mock_image_download):
    """POST /event with logo={"url": "..."} should download and save the logo."""
    pass


@pytest.mark.skip(reason="TODO")
def test_create_event_logo_as_base64(regular_user):
    """POST /event with logo={"base64File": "..."} should save the logo directly."""
    pass


# ---------------------------------------------------------------------------
# Media items upload via event creation
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="TODO")
def test_create_event_media_items_as_urls(regular_user, mock_image_download):
    """POST /event with media_items as remote URLs should download and save."""
    pass


@pytest.mark.skip(reason="TODO")
def test_create_event_media_items_as_base64(regular_user):
    """POST /event with media_items as base64 should save directly."""
    pass


# ---------------------------------------------------------------------------
# Lineup images upload via event date creation
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="TODO")
def test_add_event_date_lineup_images_as_url(regular_user, complete_event_factory, mock_image_download):
    """POST /date/event/<id> with lineup_images as remote URLs."""
    pass


@pytest.mark.skip(reason="TODO")
def test_add_event_date_lineup_images_as_base64(regular_user, complete_event_factory):
    """POST /date/event/<id> with lineup_images as base64."""
    pass


@pytest.mark.skip(reason="TODO")
def test_update_event_date_lineup_images(regular_user, event_date_factory, mock_image_download):
    """PUT /date/<id> with lineup_images should attach new lineup images."""
    pass
