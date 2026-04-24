import pytest
from flask import url_for

import pmapi.event_review.controllers as reviews
from pmapi.event_review.model import EventReview


# ---------------------------------------------------------------------------
# Event review creation
# ---------------------------------------------------------------------------


def test_add_review(regular_user, complete_event_factory):
    """POST /contribution/event/<id>/ should add a review."""
    event = complete_event_factory(creator=regular_user)
    rv = regular_user.client.post(
        url_for("event_review.AddEventReviewResource", event_id=event.id),
        json={"text": "Amazing festival!"},
    )
    assert rv.status_code == 200
    assert rv.json["text"] == "Amazing festival!"


def test_add_review_with_event_date(regular_user, complete_event_factory):
    """Adding a review with event_date_id should link it."""
    event = complete_event_factory(creator=regular_user)
    event_date = event.event_dates[0]
    rv = regular_user.client.post(
        url_for("event_review.AddEventReviewResource", event_id=event.id),
        json={"text": "Great vibes", "event_date_id": event_date.id},
    )
    assert rv.status_code == 200
    assert rv.json["event_date_id"] == event_date.id


def test_get_review_and_children(anon_user, regular_user, complete_event_factory):
    """GET /contribution/<review_id> should return review with children."""
    event = complete_event_factory(creator=regular_user)
    parent = reviews.add_review(event.id, text="Parent review", creator=regular_user)
    child = reviews.add_review(
        event.id, text="Child reply", parent_id=parent.id, creator=regular_user
    )

    rv = anon_user.client.get(
        url_for("event_review.EventReviewResource", review_id=parent.id)
    )
    assert rv.status_code == 200
    assert rv.json["text"] == "Parent review"


def test_delete_review(regular_user, complete_event_factory):
    """DELETE /contribution/<review_id> should remove the review."""
    event = complete_event_factory(creator=regular_user)
    review = reviews.add_review(event.id, text="To delete", creator=regular_user)

    rv = regular_user.client.delete(
        url_for("event_review.EventReviewResource", review_id=review.id)
    )
    assert rv.status_code == 200
    assert EventReview.query.get(review.id) is None


# ---------------------------------------------------------------------------
# Voting
# ---------------------------------------------------------------------------


def test_review_vote_up(regular_user, complete_event_factory, db):
    """Upvoting a review should increment score."""
    event = complete_event_factory(creator=regular_user)
    review = reviews.add_review(event.id, text="Vote me up", creator=regular_user)
    initial_score = review.score

    vote_status = review.vote(regular_user.id, 1)

    db.session.refresh(review)
    assert vote_status == 1
    assert review.score == initial_score + 1


def test_review_vote_down(regular_user, complete_event_factory, db):
    """Downvoting a review should decrement score."""
    event = complete_event_factory(creator=regular_user)
    review = reviews.add_review(event.id, text="Vote me down", creator=regular_user)
    initial_score = review.score

    vote_status = review.vote(regular_user.id, -1)

    db.session.refresh(review)
    assert vote_status == -1
    assert review.score == initial_score - 1


def test_review_unvote_up(regular_user, complete_event_factory, db):
    """Upvoting again should remove the upvote."""
    event = complete_event_factory(creator=regular_user)
    review = reviews.add_review(event.id, text="Unvote test", creator=regular_user)
    review.vote(regular_user.id, 1)
    db.session.refresh(review)
    score_after_up = review.score

    vote_status = review.vote(regular_user.id, 1)

    db.session.refresh(review)
    assert vote_status == -1  # returns status change
    assert review.score == score_after_up - 1


def test_review_switch_vote(regular_user, complete_event_factory, db):
    """Switching from upvote to downvote should adjust score correctly."""
    event = complete_event_factory(creator=regular_user)
    review = reviews.add_review(event.id, text="Switch vote", creator=regular_user)
    review.vote(regular_user.id, 1)
    db.session.refresh(review)

    vote_status = review.vote(regular_user.id, -1)

    db.session.refresh(review)
    assert vote_status == -2
    assert review.score == -1  # started at 0, upvoted to 1, then downvoted to -1


def test_has_voted(regular_user, complete_event_factory):
    """has_voted should return correct state."""
    event = complete_event_factory(creator=regular_user)
    review = reviews.add_review(event.id, text="Has voted test", creator=regular_user)

    assert review.has_voted(regular_user.id) == 0
    review.vote(regular_user.id, 1)
    assert review.has_voted(regular_user.id) == 1


# ---------------------------------------------------------------------------
# Hotness
# ---------------------------------------------------------------------------


def test_review_get_hotness(regular_user, complete_event_factory):
    """get_hotness should return a numeric value."""
    event = complete_event_factory(creator=regular_user)
    review = reviews.add_review(event.id, text="Hotness test", creator=regular_user)

    hotness = review.get_hotness()
    assert isinstance(hotness, float)


def test_review_get_age(regular_user, complete_event_factory):
    """Review should have a get_age method (used by hotness)."""
    event = complete_event_factory(creator=regular_user)
    review = reviews.add_review(event.id, text="Age test", creator=regular_user)

    # get_age returns seconds since epoch minus a constant
    age = review.get_age()
    assert isinstance(age, int) or isinstance(age, float)


# ---------------------------------------------------------------------------
# Model utility methods
# ---------------------------------------------------------------------------


def test_review_to_dict(regular_user, complete_event_factory):
    """to_dict should serialize basic review fields."""
    event = complete_event_factory(creator=regular_user)
    review = reviews.add_review(event.id, text="Dict test", creator=regular_user)

    d = review.to_dict()
    assert d["text"] == "Dict test"
    assert d["event_id"] == event.id
    assert "votes" in d


def test_review_get_upvoter_ids(regular_user, complete_event_factory):
    """get_upvoter_ids should return list after upvote."""
    event = complete_event_factory(creator=regular_user)
    review = reviews.add_review(event.id, text="Upvoters test", creator=regular_user)
    review.vote(regular_user.id, 1)

    upvoters = review.get_upvoter_ids()
    assert len(upvoters) == 1


def test_review_get_downvoter_ids(regular_user, complete_event_factory):
    """get_downvoter_ids should return list after downvote."""
    event = complete_event_factory(creator=regular_user)
    review = reviews.add_review(event.id, text="Downvoters test", creator=regular_user)
    review.vote(regular_user.id, -1)

    downvoters = review.get_downvoter_ids()
    assert len(downvoters) == 1
