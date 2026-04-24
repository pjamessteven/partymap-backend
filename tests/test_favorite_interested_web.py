import pytest
from flask import url_for


# ---------------------------------------------------------------------------
# Favorite endpoints
# ---------------------------------------------------------------------------


def test_favorite_event(regular_user, complete_event_factory):
    """PUT /event/<id>/favorite?favorited=true should favorite the event."""
    event = complete_event_factory(creator=regular_user)

    rv = regular_user.client.put(
        url_for("events.EventFavoriteResource", event_id=event.id),
        json={"favorited": True}
    )
    assert rv.status_code == 200
    assert rv.json["is_favorited"] is True


def test_unfavorite_event(regular_user, complete_event_factory):
    """PUT /event/<id>/favorite?favorited=false should unfavorite the event."""
    event = complete_event_factory(creator=regular_user)

    # favorite first
    rv = regular_user.client.put(
        url_for("events.EventFavoriteResource", event_id=event.id),
        json={"favorited": True}
    )
    assert rv.status_code == 200
    assert rv.json["is_favorited"] is True

    # now unfavorite
    rv = regular_user.client.put(
        url_for("events.EventFavoriteResource", event_id=event.id),
        json={"favorited": False}
    )
    assert rv.status_code == 200
    assert rv.json["is_favorited"] is False


def test_favorite_event_anon_forbidden(anon_user, complete_event_factory):
    """Anonymous user cannot favorite (should require login)."""
    event = complete_event_factory()

    rv = anon_user.client.put(
        url_for("events.EventFavoriteResource", event_id=event.id),
        json={"favorited": True}
    )
    assert rv.status_code == 302


# ---------------------------------------------------------------------------
# Interested / Going endpoints
# ---------------------------------------------------------------------------


def test_toggle_interested(regular_user, complete_event_factory):
    """POST /date/<id>/interested should add user to interested list."""
    event = complete_event_factory(creator=regular_user)
    event_date = event.event_dates[0]

    rv = regular_user.client.post(
        url_for("dates.DateUserInterestedResource", id=event_date.id)
    )
    assert rv.status_code == 200
    assert rv.json["user_interested"] is True


def test_toggle_interested_off(regular_user, complete_event_factory):
    """POST /date/<id>/interested again should remove user from interested list."""
    event = complete_event_factory(creator=regular_user)
    event_date = event.event_dates[0]

    rv = regular_user.client.post(
        url_for("dates.DateUserInterestedResource", id=event_date.id)
    )
    assert rv.status_code == 200
    assert rv.json["user_interested"] is True

    # toggle off
    rv = regular_user.client.post(
        url_for("dates.DateUserInterestedResource", id=event_date.id)
    )
    assert rv.status_code == 200
    assert rv.json["user_interested"] is False


def test_toggle_going(regular_user, complete_event_factory):
    """POST /date/<id>/going should add user to going list."""
    event = complete_event_factory(creator=regular_user)
    event_date = event.event_dates[0]

    rv = regular_user.client.post(
        url_for("dates.DateUserGoingResource", id=event_date.id)
    )
    assert rv.status_code == 200
    assert rv.json["user_going"] is True


def test_toggle_going_off(regular_user, complete_event_factory):
    """POST /date/<id>/going again should remove user from going list."""
    event = complete_event_factory(creator=regular_user)
    event_date = event.event_dates[0]

    rv = regular_user.client.post(
        url_for("dates.DateUserGoingResource", id=event_date.id)
    )
    assert rv.status_code == 200
    assert rv.json["user_going"] is True

    # toggle off
    rv = regular_user.client.post(
        url_for("dates.DateUserGoingResource", id=event_date.id)
    )
    assert rv.status_code == 200
    assert rv.json["user_going"] is False


def test_toggle_interested_anon_forbidden(anon_user, complete_event_factory):
    """Anonymous user cannot mark interested."""
    event = complete_event_factory()
    event_date = event.event_dates[0]

    rv = anon_user.client.post(
        url_for("dates.DateUserInterestedResource", id=event_date.id)
    )
    assert rv.status_code == 302


def test_toggle_going_anon_forbidden(anon_user, complete_event_factory):
    """Anonymous user cannot mark going."""
    event = complete_event_factory()
    event_date = event.event_dates[0]

    rv = anon_user.client.post(
        url_for("dates.DateUserGoingResource", id=event_date.id)
    )
    assert rv.status_code == 302


# ---------------------------------------------------------------------------
# ICS download
# ---------------------------------------------------------------------------


def test_ics_download(complete_event_factory, anon_user):
    """GET /date/<id>/ics should return a valid .ics calendar file."""
    event = complete_event_factory()
    event_date = event.event_dates[0]

    rv = anon_user.client.get(
        url_for("dates.DateIcsDownloadResource", id=event_date.id)
    )
    assert rv.status_code == 200
    assert "text/calendar" in rv.content_type
    assert b"BEGIN:VCALENDAR" in rv.data
    assert str(event_date.event.name) in rv.data.decode("utf-8")
