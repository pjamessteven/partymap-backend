import pytest
from flask import url_for


# ---------------------------------------------------------------------------
# Favorite endpoints
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="TODO")
def test_favorite_event(regular_user, complete_event_factory):
    """PUT /event/<id>/favorite?favorited=true should favorite the event."""
    pass


@pytest.mark.skip(reason="TODO")
def test_unfavorite_event(regular_user, complete_event_factory):
    """PUT /event/<id>/favorite?favorited=false should unfavorite the event."""
    pass


@pytest.mark.skip(reason="TODO")
def test_favorite_event_anon_forbidden(anon_user, complete_event_factory):
    """Anonymous user cannot favorite (should require login)."""
    pass


# ---------------------------------------------------------------------------
# Interested / Going endpoints
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="TODO")
def test_toggle_interested(regular_user, complete_event_factory):
    """POST /date/<id>/interested should add user to interested list."""
    pass


@pytest.mark.skip(reason="TODO")
def test_toggle_interested_off(regular_user, complete_event_factory):
    """POST /date/<id>/interested again should remove user from interested list."""
    pass


@pytest.mark.skip(reason="TODO")
def test_toggle_going(regular_user, complete_event_factory):
    """POST /date/<id>/going should add user to going list."""
    pass


@pytest.mark.skip(reason="TODO")
def test_toggle_going_off(regular_user, complete_event_factory):
    """POST /date/<id>/going again should remove user from going list."""
    pass


@pytest.mark.skip(reason="TODO")
def test_toggle_interested_anon_forbidden(anon_user, complete_event_factory):
    """Anonymous user cannot mark interested."""
    pass


@pytest.mark.skip(reason="TODO")
def test_toggle_going_anon_forbidden(anon_user, complete_event_factory):
    """Anonymous user cannot mark going."""
    pass


# ---------------------------------------------------------------------------
# ICS download
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="TODO")
def test_ics_download(complete_event_factory, anon_user):
    """GET /date/<id>/ics should return a valid .ics calendar file."""
    pass
