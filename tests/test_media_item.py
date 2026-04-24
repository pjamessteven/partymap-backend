from flask import url_for
import pmapi.media_item.controllers as media_items


def test_update_media_item_caption(regular_user, complete_event_factory, mock_image_download):
    """PUT /media/<id> with caption should update the caption."""
    event = complete_event_factory(creator=regular_user)
    media_items.add_media_to_event(
        [{"url": "https://example.com/test.jpg", "caption": "Old caption"}],
        event,
        creator=regular_user,
    )
    item = event.media_items[0]

    rv = regular_user.client.put(
        url_for("media.MediaItemResource", id=item.id),
        json={"caption": "New caption"},
    )
    assert rv.status_code == 200
    assert rv.json["caption"] == "New caption"


def test_update_media_item_position(regular_user, complete_event_factory, mock_image_download):
    """PUT /media/<id> with position should reorder the media item."""
    event = complete_event_factory(creator=regular_user)
    media_items.add_media_to_event(
        [{"url": "https://example.com/test1.jpg"}, {"url": "https://example.com/test2.jpg"}],
        event,
        creator=regular_user,
    )
    assert len(event.media_items) == 2
    first_item = event.media_items[0]
    second_item = event.media_items[1]

    # Move second item to position 0
    rv = regular_user.client.put(
        url_for("media.MediaItemResource", id=second_item.id),
        json={"position": 0},
    )
    assert rv.status_code == 200
    # After reorder, second_item should be at position 0
    assert second_item.position == 0


def test_update_media_item_unauthorized(regular_user_factory, complete_event_factory, mock_image_download):
    """PUT /media/<id> as non-creator should return 403."""
    user1 = regular_user_factory()
    user2 = regular_user_factory()
    event = complete_event_factory(creator=user1)
    media_items.add_media_to_event(
        [{"url": "https://example.com/test.jpg"}],
        event,
        creator=user1,
    )
    item = event.media_items[0]

    rv = user2.client.put(
        url_for("media.MediaItemResource", id=item.id),
        json={"caption": "Hacked"},
    )
    assert rv.status_code == 403


def test_delete_item_by_id_controller(regular_user, complete_event_factory, mock_image_download):
    """Controller delete_item_by_id should remove the item."""
    event = complete_event_factory(creator=regular_user)
    media_items.add_media_to_event(
        [{"url": "https://example.com/test.jpg"}],
        event,
        creator=regular_user,
    )
    item = event.media_items[0]
    item_id = item.id

    result, status = media_items.delete_item_by_id(item_id)
    assert status == 204

    # Verify item is gone
    assert media_items.get_media_item_by_id(item_id) is None


def test_remove_all_media_from_event(regular_user, complete_event_factory, mock_image_download):
    """Controller remove_all_media_from_event should delete all media."""
    from pmapi.extensions import db
    from pmapi.media_item.model import MediaItem

    event = complete_event_factory(creator=regular_user)
    media_items.add_media_to_event(
        [
            {"url": "https://example.com/test1.jpg"},
            {"url": "https://example.com/test2.jpg"},
        ],
        event,
        creator=regular_user,
    )
    assert len(event.media_items) == 2

    media_items.remove_all_media_from_event(event)
    db.session.commit()

    # Query fresh count from DB
    count = db.session.query(MediaItem).filter(MediaItem.event_id == event.id).count()
    assert count == 0


def test_get_media_item_or_404_not_found():
    """get_media_item_or_404 should raise RecordNotFound for bad id."""
    from pmapi.exceptions import RecordNotFound
    with pytest.raises(RecordNotFound):
        media_items.get_media_item_or_404(999999)


import pytest
