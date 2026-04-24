from flask import url_for
import pytest

import pmapi.event_artist.controllers as artists
from pmapi.event_artist.model import Artist, ArtistTag, ArtistUrl


# ---------------------------------------------------------------------------
# Artist URLs
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Artist URLs
# ---------------------------------------------------------------------------


def test_add_artist_url(db, event_date_factory):
    """add_artist_url should create an ArtistUrl record."""
    event_date = event_date_factory()
    eda = artists.add_artist_to_date(event_date, name="URL Artist")

    artists.add_artist_url("https://soundcloud.com/artist", "soundcloud", eda.artist)

    db.session.refresh(eda.artist)
    types = [u.type for u in eda.artist.urls]
    assert "soundcloud" in types


def test_delete_artist_url(db, event_date_factory):
    """delete_artist_url should remove an ArtistUrl record."""
    event_date = event_date_factory()
    eda = artists.add_artist_to_date(event_date, name="URL Artist")
    artists.add_artist_url("https://soundcloud.com/artist", "soundcloud", eda.artist)
    url_id = eda.artist.urls[0].id

    artists.delete_artist_url(url_id)

    assert ArtistUrl.query.get(url_id) is None


# ---------------------------------------------------------------------------
# Artist Tags
# ---------------------------------------------------------------------------


def test_add_tags_to_artist(db, event_date_factory):
    """Adding tags to an artist should create ArtistTag records."""
    event_date = event_date_factory()
    eda = artists.add_artist_to_date(event_date, name="Tagged Artist")

    artists.add_tags_to_artist(["techno", "house"], eda.artist)

    db.session.refresh(eda.artist)
    tag_ids = [t.tag_id for t in eda.artist.artist_tags]
    assert "techno" in tag_ids
    assert "house" in tag_ids


def test_remove_tags_from_artist(db, event_date_factory):
    """Removing tags from an artist should delete ArtistTag records."""
    event_date = event_date_factory()
    eda = artists.add_artist_to_date(event_date, name="Untagged Artist")
    artists.add_tags_to_artist(["techno", "house"], eda.artist)

    artists.remove_tags_from_artist(["techno"], eda.artist)

    db.session.refresh(eda.artist)
    tag_ids = [t.tag_id for t in eda.artist.artist_tags]
    assert "techno" not in tag_ids
    assert "house" in tag_ids


# ---------------------------------------------------------------------------
# Artist query filters
# ---------------------------------------------------------------------------


def test_get_artists_by_name_query(anon_user, event_date_factory):
    """get_artists with query should filter by name."""
    event_date = event_date_factory()
    artists.add_artist_to_date(event_date, name="UniqueArtistName")

    result = artists.get_artists(query="UniqueArtistName")
    names = [a.name for a in result.items]
    assert "UniqueArtistName" in names


def test_get_artist_by_exact_name(event_date_factory):
    """get_artist_by_exact_name should find exact match."""
    event_date = event_date_factory()
    eda = artists.add_artist_to_date(event_date, name="ExactMatch")

    found = artists.get_artist_by_exact_name("ExactMatch")
    assert found is not None
    assert found.name == "ExactMatch"


def test_get_artist_by_exact_name_not_found():
    """get_artist_by_exact_name should return None for nonexistent name."""
    found = artists.get_artist_by_exact_name("NonExistentArtist12345")
    assert found is None


def test_get_artist_or_404_found(event_date_factory):
    """get_artist_or_404 should return artist when found."""
    event_date = event_date_factory()
    eda = artists.add_artist_to_date(event_date, name="Found Artist")

    found = artists.get_artist_or_404(eda.artist.id)
    assert found.name == "Found Artist"


def test_get_artist_or_404_not_found():
    """get_artist_or_404 should raise RecordNotFound when missing."""
    import pmapi.exceptions as exc
    with pytest.raises(exc.RecordNotFound):
        artists.get_artist_or_404(999999)


# ---------------------------------------------------------------------------
# Update artist
# ---------------------------------------------------------------------------


def test_update_artist_name(event_date_factory, db):
    """update_artist should change the artist name."""
    event_date = event_date_factory()
    eda = artists.add_artist_to_date(event_date, name="Old Name")

    artists.update_artist(eda.artist.id, name="New Name")

    db.session.refresh(eda.artist)
    assert eda.artist.name == "New Name"


def test_update_artist_description(event_date_factory, db):
    """update_artist should change the artist description."""
    event_date = event_date_factory()
    eda = artists.add_artist_to_date(event_date, name="Desc Artist")

    artists.update_artist(eda.artist.id, description="A great DJ")

    db.session.refresh(eda.artist)
    assert eda.artist.description == "A great DJ"


# ---------------------------------------------------------------------------
# Delete artist
# ---------------------------------------------------------------------------


def test_delete_artist(event_date_factory, db):
    """delete_artist should remove the artist."""
    event_date = event_date_factory()
    eda = artists.add_artist_to_date(event_date, name="To Delete")
    artist_id = eda.artist.id

    artists.delete_artist(artist_id)

    assert Artist.query.get(artist_id) is None


# ---------------------------------------------------------------------------
# Artist on event date CRUD
# ---------------------------------------------------------------------------


def test_add_artist_to_date_creates_artist(event_date_factory):
    """add_artist_to_date should create an artist and link to event date."""
    event_date = event_date_factory()
    eda = artists.add_artist_to_date(event_date, name="Lineup Artist")

    assert eda.id is not None
    assert len(event_date.artists) == 1
    assert event_date.artists[0].artist.name == "Lineup Artist"


def test_add_artist_to_date_with_stage_and_time(event_date_factory):
    """add_artist_to_date should accept stage and start_naive."""
    event_date = event_date_factory()
    start_str = "2026-07-15T20:00:00"
    eda = artists.add_artist_to_date(
        event_date, name="Timed Artist", stage="Main Stage", start_naive=start_str
    )

    from datetime import datetime
    assert eda.stage == "Main Stage"
    assert eda.start_naive == datetime(2026, 7, 15, 20, 0, 0)


def test_remove_artists_from_date(event_date_factory, db):
    """remove_artists_from_date should unlink artists from event date."""
    event_date = event_date_factory()
    eda = artists.add_artist_to_date(event_date, name="Removable")

    artists.remove_artists_from_date(event_date, [{"id": eda.id}])

    db.session.refresh(event_date)
    assert len(event_date.artists) == 0


def test_update_artists_of_date(event_date_factory, db):
    """update_artists_of_date should modify artist start time on event date."""
    event_date = event_date_factory()
    eda = artists.add_artist_to_date(
        event_date, name="Updateable", start_naive="2026-07-15T20:00:00"
    )

    artists.update_artists_of_date(
        event_date,
        artists=[{"id": eda.id, "start_naive": "2026-07-15T21:00:00"}],
    )

    db.session.commit()
    db.session.refresh(eda)
    assert eda.start_naive.hour == 21
