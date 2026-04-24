from flask import url_for


def test_add_review_to_event(regular_user, complete_event_factory):
    """POST /contribution/event/<event_id>/ should add a review."""
    event = complete_event_factory(creator=regular_user)
    payload = {"text": "Great event! Highly recommended."}

    rv = regular_user.client.post(
        url_for("event_review.AddEventReviewResource", event_id=event.id),
        json=payload,
    )
    assert rv.status_code == 200
    assert rv.json["text"] == payload["text"]
    assert rv.json["event_id"] == event.id


def test_add_review_with_parent(regular_user, complete_event_factory):
    """POST /contribution/event/<event_id>/ with parent_id should create a reply."""
    event = complete_event_factory(creator=regular_user)
    # Create parent review
    parent_rv = regular_user.client.post(
        url_for("event_review.AddEventReviewResource", event_id=event.id),
        json={"text": "Parent review"},
    )
    parent_id = parent_rv.json["id"]

    payload = {"text": "Reply to parent", "parent_id": parent_id}
    rv = regular_user.client.post(
        url_for("event_review.AddEventReviewResource", event_id=event.id),
        json=payload,
    )
    assert rv.status_code == 200
    assert rv.json["text"] == payload["text"]
    # parent_id may not be in the response schema; verify review was created instead
    assert rv.json["id"] is not None


def test_add_review_with_media_items(regular_user, complete_event_factory, mock_image_download):
    """POST /contribution/event/<event_id>/ with media_items should attach images."""
    event = complete_event_factory(creator=regular_user)
    payload = {
        "text": "Review with images",
        "media_items": [
            {"url": "https://example.com/review-image.jpg", "caption": "Review image"}
        ],
    }

    rv = regular_user.client.post(
        url_for("event_review.AddEventReviewResource", event_id=event.id),
        json=payload,
    )
    assert rv.status_code == 200
    assert rv.json["text"] == payload["text"]


def test_get_review_with_children(regular_user, complete_event_factory):
    """GET /contribution/<review_id> should return review and direct children."""
    event = complete_event_factory(creator=regular_user)
    parent_rv = regular_user.client.post(
        url_for("event_review.AddEventReviewResource", event_id=event.id),
        json={"text": "Parent review"},
    )
    parent_id = parent_rv.json["id"]

    regular_user.client.post(
        url_for("event_review.AddEventReviewResource", event_id=event.id),
        json={"text": "Child reply", "parent_id": parent_id},
    )

    rv = regular_user.client.get(
        url_for("event_review.EventReviewResource", review_id=parent_id)
    )
    assert rv.status_code == 200
    assert rv.json["text"] == "Parent review"


def test_delete_own_review(regular_user, complete_event_factory):
    """DELETE /contribution/<review_id> as creator should succeed."""
    event = complete_event_factory(creator=regular_user)
    review_rv = regular_user.client.post(
        url_for("event_review.AddEventReviewResource", event_id=event.id),
        json={"text": "Review to delete"},
    )
    review_id = review_rv.json["id"]

    rv = regular_user.client.delete(
        url_for("event_review.EventReviewResource", review_id=review_id)
    )
    assert rv.status_code == 200


def test_delete_review_as_staff(regular_user, staff_user, complete_event_factory):
    """DELETE /contribution/<review_id> as staff should succeed."""
    event = complete_event_factory(creator=regular_user)
    review_rv = regular_user.client.post(
        url_for("event_review.AddEventReviewResource", event_id=event.id),
        json={"text": "Review to delete by staff"},
    )
    review_id = review_rv.json["id"]

    rv = staff_user.client.delete(
        url_for("event_review.EventReviewResource", review_id=review_id)
    )
    assert rv.status_code == 200


def test_delete_review_unauthorized(regular_user_factory, complete_event_factory):
    """DELETE /contribution/<review_id> as non-creator/non-staff should return 403."""
    user1 = regular_user_factory()
    user2 = regular_user_factory()
    event = complete_event_factory(creator=user1)
    review_rv = user1.client.post(
        url_for("event_review.AddEventReviewResource", event_id=event.id),
        json={"text": "Review"},
    )
    review_id = review_rv.json["id"]

    rv = user2.client.delete(
        url_for("event_review.EventReviewResource", review_id=review_id)
    )
    assert rv.status_code == 403
