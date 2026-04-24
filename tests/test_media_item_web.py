from flask import url_for


def test_delete_media_item_as_creator(regular_user, complete_event_factory, mock_image_download):
    """DELETE /media/<id> as event creator should succeed."""
    event = complete_event_factory(creator=regular_user)
    # Add a media item to the event
    from pmapi.media_item.controllers import add_media_to_event
    add_media_to_event([{"url": "https://example.com/test.jpg"}], event, creator=regular_user)

    # Get the first media item
    media_item = event.media_items[0]
    rv = regular_user.client.delete(url_for("media.MediaItemResource", id=media_item.id))
    # Endpoint returns 204 on success
    assert rv.status_code == 204


def test_delete_media_item_unauthorized(regular_user_factory, complete_event_factory, mock_image_download):
    """DELETE /media/<id> as non-creator/non-staff should return 403."""
    user1 = regular_user_factory()
    user2 = regular_user_factory()
    event = complete_event_factory(creator=user1)
    from pmapi.media_item.controllers import add_media_to_event
    add_media_to_event([{"url": "https://example.com/test.jpg"}], event, creator=user1)

    media_item = event.media_items[0]
    rv = user2.client.delete(url_for("media.MediaItemResource", id=media_item.id))
    assert rv.status_code == 403


# ---------------------------------------------------------------------------
# Logo upload via event creation
# ---------------------------------------------------------------------------


import pytest

def test_create_event_logo_as_url(regular_user, mock_image_download, mock_gmaps_resolve):
    """POST /event with logo={"url": "..."} should download and save the logo."""
    payload = {
        "name": "Event with logo",
        "description": "Test description",
        "full_description": "Full test description",
        "date_time": {"start": "2026-07-15T14:00:00", "end": "2026-07-17T23:00:00"},
        "location": {"description": "Central Park, New York, NY"},
        "logo": {"url": "https://example.com/logo.jpg"},
    }
    rv = regular_user.client.post(url_for("events.EventsResource"), json=payload)
    assert rv.status_code == 200


# ---------------------------------------------------------------------------
# Media items upload via event creation
# ---------------------------------------------------------------------------


def test_create_event_media_items_as_urls(regular_user, mock_image_download, mock_gmaps_resolve):
    """POST /event with media_items as remote URLs should download and save."""
    payload = {
        "name": "Event with media",
        "description": "Test description",
        "full_description": "Full test description",
        "date_time": {"start": "2026-07-15T14:00:00", "end": "2026-07-17T23:00:00"},
        "location": {"description": "Central Park, New York, NY"},
        "media_items": [
            {"url": "https://example.com/image1.jpg", "caption": "Image 1"},
            {"url": "https://example.com/image2.jpg", "caption": "Image 2"},
        ],
    }
    rv = regular_user.client.post(url_for("events.EventsResource"), json=payload)
    assert rv.status_code == 200


# ---------------------------------------------------------------------------
# Lineup images upload via event date creation
# ---------------------------------------------------------------------------


import pytest

def test_add_event_date_lineup_images_as_url(regular_user, complete_event_factory, mock_image_download, mock_gmaps_resolve):
    """POST /date/event/<id> with lineup_images as remote URLs."""
    event = complete_event_factory(creator=regular_user)
    payload = {
        "date_time": {"start": "2026-08-15T18:00:00", "end": "2026-08-16T01:00:00"},
        "location": {"description": "Central Park, New York, NY"},
        "lineup_images": [
            {"url": "https://example.com/lineup.jpg", "caption": "Lineup"}
        ],
    }
    rv = regular_user.client.post(
        url_for("dates.EventDatesResource", event_id=event.id), json=payload
    )
    assert rv.status_code == 200


def test_update_event_date_lineup_images(regular_user, event_date_factory, mock_image_download, mock_gmaps_resolve):
    """PUT /date/<id> with lineup_images should attach new lineup images."""
    event_date = event_date_factory()
    rv = regular_user.client.put(
        url_for("dates.DateResource", id=event_date.id),
        json={
            "lineup_images": [
                {"url": "https://example.com/new-lineup.jpg", "caption": "New Lineup"}
            ]
        },
    )
    assert rv.status_code == 200
