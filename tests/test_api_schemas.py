"""API tests based on api_schemas examples for event/eventdate endpoints."""

from datetime import datetime
from flask import url_for
import json
import pytest


def test_get_events_list(anon_user, complete_event_factory):
    """Test GET /events - list events with query params (from getEvents.example.json)"""
    complete_event_factory(name="summer festival 2026")
    complete_event_factory(name="winter festival 2026")
    complete_event_factory(name="summer concert")

    # Test query search
    rv = anon_user.client.get(url_for("events.EventsResource", query="summer festival"))
    assert rv.status_code == 200
    assert len(rv.json["items"]) == 1
    assert rv.json["items"][0]["name"] == "summer festival 2026"

    # Test pagination
    rv = anon_user.client.get(url_for("events.EventsResource", per_page=2, page=1))
    assert rv.status_code == 200
    assert len(rv.json["items"]) == 2


def test_update_event_with_api_schema(regular_user, complete_event_factory, mock_gmaps_resolve):
    """Test PUT /events/<id> - update event (from updateEvent.example.json)"""
    event = complete_event_factory(creator=regular_user)

    payload = {
        "name": "Summer Music Festival 2026 - Updated",
        "description": "An unforgettable weekend - Now with more artists!",
        "url": "https://summerfest2026.example.com",
        "add_tags": ["family-friendly", "workshops"],
        "remove_tags": ["camping"],
    }

    rv = regular_user.client.put(
        url_for("events.EventResource", event_id=event.id), json=payload
    )
    assert rv.status_code == 200
    updated = rv.json
    assert updated["name"] == payload["name"]
    assert updated["description"] == payload["description"]


def test_update_event_date_with_api_schema(regular_user, event_date_factory, mock_gmaps_resolve, mock_image_download):
    """Test PUT /dates/<id> - update event date (from updateEventDate.example.json)"""
    event_date = event_date_factory()

    payload = {
        "description": "Set times confirmed and final release tickets available.",
        "url": "https://summerfest2026.example.com/opening-night-updated",
        "size": 13500,
        "date_time": {
            "start": "2026-07-15T18:30:00",
            "end": "2026-07-16T01:30:00"
        },
        "cancelled": False,
        "add_artists": [
            {"name": "Late Night Guest", "stage": "After Hours Tent", "start_naive": "2026-07-16T00:15:00"}
        ],
        "lineup_images": [
            {"url": "https://example.com/opening-night-lineup-final.jpg", "caption": "Final lineup"}
        ]
    }

    rv = regular_user.client.put(
        url_for("dates.DateResource", id=event_date.id), json=payload
    )
    if rv.status_code != 200:
        print("EVENT DATE UPDATE ERROR:", rv.status_code, rv.data[:500])
    assert rv.status_code == 200
    updated = rv.json
    assert updated["description"] == payload["description"]
    assert updated["url"] == payload["url"]
    assert updated["size"] == payload["size"]
    assert updated["cancelled"] is False


def test_get_event_date(anon_user, complete_event_factory):
    """Test GET /dates/<id> - get single event date"""
    event = complete_event_factory()
    assert len(event.event_dates) == 1

    rv = anon_user.client.get(
        url_for("dates.DateResource", id=event.event_dates[0].id)
    )
    assert rv.status_code == 200
    assert rv.json["id"] == event.event_dates[0].id
    assert rv.json["event_id"] == event.id


def test_get_single_event(anon_user, complete_event_factory):
    """Test GET /events/<id> - get single event"""
    event = complete_event_factory()

    rv = anon_user.client.get(url_for("events.EventResource", event_id=event.id))
    assert rv.status_code == 200
    assert rv.json["id"] == event.id
    assert "event_dates" in rv.json


def test_delete_event(regular_user, complete_event_factory):
    """Test DELETE /events/<id> - delete event"""
    event = complete_event_factory(creator=regular_user)

    rv = regular_user.client.delete(
        url_for("events.EventResource", event_id=event.id)
    )
    assert rv.status_code == 204

    # Verify event is gone
    rv = regular_user.client.get(
        url_for("events.EventResource", event_id=event.id)
    )
    assert rv.status_code == 404


def test_delete_event_date(regular_user, complete_event_factory):
    """Test DELETE /dates/<id> - delete event date"""
    event = complete_event_factory(creator=regular_user)
    event_date = event.event_dates[0]

    rv = regular_user.client.delete(
        url_for("dates.DateResource", id=event_date.id)
    )
    assert rv.status_code == 200


def test_favorite_event(regular_user, complete_event_factory):
    """Test PUT /events/<id>/favorite - favorite an event"""
    event = complete_event_factory(creator=regular_user)

    rv = regular_user.client.put(
        url_for("events.EventFavoriteResource", event_id=event.id),
        json={"favorited": True}
    )
    assert rv.status_code == 200
    assert rv.json["is_favorited"] is True

    rv = regular_user.client.put(
        url_for("events.EventFavoriteResource", event_id=event.id),
        json={"favorited": False}
    )
    assert rv.status_code == 200
    assert rv.json["is_favorited"] is False


def test_mark_interested(regular_user, complete_event_factory):
    """Test POST /dates/<id>/interested - mark as interested"""
    event = complete_event_factory(creator=regular_user)
    event_date = event.event_dates[0]

    rv = regular_user.client.post(
        url_for("dates.DateUserInterestedResource", id=event_date.id)
    )
    assert rv.status_code == 200
    assert rv.json["user_interested"] is True

    # Toggle off
    rv = regular_user.client.post(
        url_for("dates.DateUserInterestedResource", id=event_date.id)
    )
    assert rv.status_code == 200
    assert rv.json["user_interested"] is False


def test_mark_going(regular_user, complete_event_factory):
    """Test POST /dates/<id>/going - mark as going"""
    event = complete_event_factory(creator=regular_user)
    event_date = event.event_dates[0]

    rv = regular_user.client.post(
        url_for("dates.DateUserGoingResource", id=event_date.id)
    )
    assert rv.status_code == 200
    assert rv.json["user_going"] is True

    # Toggle off
    rv = regular_user.client.post(
        url_for("dates.DateUserGoingResource", id=event_date.id)
    )
    assert rv.status_code == 200
    assert rv.json["user_going"] is False


def test_get_event_activity(anon_user, complete_event_factory):
    """Test GET /events/<id>/activity - get event activity"""
    event = complete_event_factory()

    rv = anon_user.client.get(
        url_for("events.EventActivityResource", event_id=event.id)
    )
    assert rv.status_code == 200
    assert "items" in rv.json


def test_get_event_contributors(anon_user, complete_event_factory):
    """Test GET /events/<id>/contributors - get event contributors"""
    event = complete_event_factory()

    rv = anon_user.client.get(
        url_for("events.EventContributorsResource", event_id=event.id)
    )
    assert rv.status_code == 200
    assert "items" in rv.json


def test_query_event_dates(anon_user, complete_event_factory):
    """Test GET /dates - list event dates with filters"""
    complete_event_factory(name="summer festival")
    complete_event_factory(name="winter festival")

    rv = anon_user.client.get(url_for("dates.DatesResource"))
    assert rv.status_code == 200
    assert len(rv.json["items"]) >= 2

    # Test query filter
    rv = anon_user.client.get(
        url_for("dates.DatesResource", query="summer")
    )
    assert rv.status_code == 200


def test_add_event_date_with_api_schema(regular_user, complete_event_factory, mock_gmaps_resolve, mock_image_download):
    """Test POST /dates/event/<event_id> - add event date (from addEventDate.example.json)"""
    event = complete_event_factory(creator=regular_user)

    payload = {
        "description": "Opening night with extended set times and outdoor projections.",
        "url": "https://summerfest2026.example.com/opening-night",
        "size": 12000,
        "date_time": {
            "start": "2026-07-15T18:00:00",
            "end": "2026-07-16T01:00:00"
        },
        "location": {
            "description": "Central Park, New York, NY"
        },
        "artists": [
            {"name": "The Headliners", "stage": "Main Stage", "start_naive": "2026-07-15T22:00:00"},
            {"name": "Support Act One", "stage": "Main Stage", "start_naive": "2026-07-15T20:30:00"}
        ],
        "lineup_images": [
            {"url": "https://example.com/opening-night-lineup.jpg", "caption": "Opening night lineup poster"}
        ]
    }

    rv = regular_user.client.post(
        url_for("dates.EventDatesResource", event_id=event.id), json=payload
    )
    assert rv.status_code == 200
    result = rv.json
    assert result["id"] == event.id
    assert len(result["event_dates"]) >= 2


def test_get_event_versions(anon_user, complete_event_factory):
    """Test GET /events/<id>/versions - get event versions"""
    event = complete_event_factory()

    rv = anon_user.client.get(
        url_for("events.EventVersionsResource", event_id=event.id)
    )
    assert rv.status_code == 200
    assert "items" in rv.json


def test_get_event_contributions(anon_user, complete_event_factory):
    """Test GET /events/<id>/contributions - get event contributions"""
    event = complete_event_factory()

    rv = anon_user.client.get(
        url_for("events.EventContributionResource", event_id=event.id)
    )
    assert rv.status_code == 200
    assert "items" in rv.json
