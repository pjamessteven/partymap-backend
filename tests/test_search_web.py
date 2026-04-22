import pytest
from flask import url_for


# ---------------------------------------------------------------------------
# Search endpoint
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="TODO")
def test_search_with_query(anon_user, complete_event_factory):
    """GET /search/?query=... should return matching events, tags, locations, artists."""
    pass


@pytest.mark.skip(reason="TODO")
def test_search_empty_query(anon_user):
    """GET /search/?query= (empty) should handle gracefully."""
    pass


@pytest.mark.skip(reason="TODO")
def test_search_no_results(anon_user):
    """GET /search/?query=nonexistent should return empty results."""
    pass
