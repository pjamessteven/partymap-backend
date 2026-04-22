import pytest
from flask import url_for


# ---------------------------------------------------------------------------
# Artist CRUD endpoints
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="TODO")
def test_get_artist(anon_user):
    """GET /artist/<id> should return artist info."""
    pass


@pytest.mark.skip(reason="TODO")
def test_get_artists_list(anon_user):
    """GET /artist/ should return paginated list of artists."""
    pass


@pytest.mark.skip(reason="TODO")
def test_search_artists(anon_user):
    """GET /artist/?query=... should search artists by name."""
    pass


@pytest.mark.skip(reason="TODO")
def test_update_artist(regular_user):
    """PUT /artist/<id> should update artist info."""
    pass


@pytest.mark.skip(reason="TODO")
def test_delete_artist_as_admin(admin_user):
    """DELETE /artist/<id> as admin should succeed."""
    pass


@pytest.mark.skip(reason="TODO")
def test_delete_artist_unauthorized(regular_user_factory):
    """DELETE /artist/<id> as non-admin should return 403."""
    pass


# ---------------------------------------------------------------------------
# Artist suggestions
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="TODO")
def test_suggest_artist_edit_as_anon(anon_user, mock_hcaptcha):
    """PUT /artist/<id>/suggest as anon with hCaptcha should create suggestion."""
    pass


@pytest.mark.skip(reason="TODO")
def test_suggest_artist_delete_as_anon(anon_user, mock_hcaptcha):
    """DELETE /artist/<id>/suggest as anon with hCaptcha should create suggestion."""
    pass


# ---------------------------------------------------------------------------
# Artist refresh
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="TODO")
def test_refresh_artist_info(admin_user):
    """GET /artist/<id>/refresh should refresh artist from Musicbrainz/Last.fm."""
    pass


# ---------------------------------------------------------------------------
# Artists on event dates
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="TODO")
def test_add_artists_to_event_date(regular_user, complete_event_factory):
    """POST /date/event/<id> with artists should add them to the date."""
    pass


@pytest.mark.skip(reason="TODO")
def test_remove_artists_from_event_date(regular_user, event_date_factory):
    """PUT /date/<id> with remove_artists should remove artists."""
    pass


@pytest.mark.skip(reason="TODO")
def test_update_artist_set_times(regular_user, event_date_factory):
    """PUT /date/<id> with update_artists should modify artist start_naive times."""
    pass
