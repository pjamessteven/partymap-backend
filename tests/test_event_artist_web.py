from flask import url_for


def test_get_artist(anon_user, event_date_factory):
    """GET /artist/<id> should return artist info."""
    event_date = event_date_factory()
    # Add an artist to the event date
    from pmapi.event_artist.controllers import add_artist_to_date
    eda = add_artist_to_date(event_date, name="Test Artist")

    rv = anon_user.client.get(url_for("artists.ArtistResource", id=eda.artist.id))
    assert rv.status_code == 200
    assert rv.json["name"] == "Test Artist"


def test_get_artists_list(anon_user):
    """GET /artist/ should return paginated list of artists."""
    rv = anon_user.client.get(url_for("artists.ArtistsResource"))
    assert rv.status_code == 200
    assert "items" in rv.json


def test_search_artists(anon_user, event_date_factory):
    """GET /artist/?query=... should search artists by name."""
    event_date = event_date_factory()
    from pmapi.event_artist.controllers import add_artist_to_date
    add_artist_to_date(event_date, name="UniqueSearchArtist")

    rv = anon_user.client.get(url_for("artists.ArtistsResource", query="UniqueSearchArtist"))
    assert rv.status_code == 200


import pytest

def test_update_artist_as_staff(staff_user, event_date_factory):
    """PUT /artist/<id> as staff should update artist info."""
    event_date = event_date_factory()
    from pmapi.event_artist.controllers import add_artist_to_date
    eda = add_artist_to_date(event_date, name="Old Name")

    rv = staff_user.client.put(
        url_for("artists.ArtistResource", id=eda.artist.id),
        query_string={"name": "Updated Name"},
    )
    assert rv.status_code == 200
    assert rv.json["name"] == "Updated Name"


def test_delete_artist_as_admin(admin_user, event_date_factory):
    """DELETE /artist/<id> as admin should succeed."""
    event_date = event_date_factory()
    from pmapi.event_artist.controllers import add_artist_to_date
    eda = add_artist_to_date(event_date, name="Artist To Delete")

    rv = admin_user.client.delete(url_for("artists.ArtistResource", id=eda.artist.id))
    assert rv.status_code == 204


def test_delete_artist_unauthorized(regular_user_factory, event_date_factory):
    """DELETE /artist/<id> as non-admin should return 403."""
    user = regular_user_factory()
    event_date = event_date_factory()
    from pmapi.event_artist.controllers import add_artist_to_date
    eda = add_artist_to_date(event_date, name="Protected Artist")

    rv = user.client.delete(url_for("artists.ArtistResource", id=eda.artist.id))
    assert rv.status_code == 403


# ---------------------------------------------------------------------------
# Artists on event dates
# ---------------------------------------------------------------------------


def test_add_artists_to_event_date(regular_user, complete_event_factory, mock_gmaps_resolve):
    """POST /date/event/<id> with artists should add them to the date."""
    event = complete_event_factory(creator=regular_user)
    payload = {
        "date_time": {"start": "2026-08-15T18:00:00", "end": "2026-08-16T01:00:00"},
        "location": {"description": "Central Park, New York, NY"},
        "artists": [
            {"name": "New Stage Artist", "stage": "Main Stage"},
        ],
    }
    rv = regular_user.client.post(
        url_for("dates.EventDatesResource", event_id=event.id), json=payload
    )
    assert rv.status_code == 200


def test_remove_artists_from_event_date(regular_user, event_date_factory, mock_gmaps_resolve):
    """PUT /date/<id> with remove_artists should remove artists."""
    event_date = event_date_factory()
    from pmapi.event_artist.controllers import add_artist_to_date
    artist = add_artist_to_date(event_date, name="Removable Artist")

    rv = regular_user.client.put(
        url_for("dates.DateResource", id=event_date.id),
        json={"remove_artists": [{"id": artist.id}]},
    )
    assert rv.status_code == 200


def test_update_artist_set_times(regular_user, event_date_factory, mock_gmaps_resolve):
    """PUT /date/<id> with update_artists should modify artist start_naive times."""
    event_date = event_date_factory()
    from pmapi.event_artist.controllers import add_artist_to_date
    artist = add_artist_to_date(event_date, name="Time Update Artist", start_naive="2026-07-15T20:00:00")

    rv = regular_user.client.put(
        url_for("dates.DateResource", id=event_date.id),
        json={"update_artists": [{"id": artist.id, "start_naive": "2026-07-15T21:00:00"}]},
    )
    assert rv.status_code == 200
