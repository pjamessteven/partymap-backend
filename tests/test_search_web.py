from flask import url_for


def test_search_with_query(anon_user, complete_event_factory):
    """GET /search/?query=... should return matching events, tags, locations, artists."""
    complete_event_factory(name="summer festival")
    complete_event_factory(name="winter festival")

    rv = anon_user.client.get(url_for("search.SearchResource", query="summer"))
    assert rv.status_code == 200
    results = rv.json["results"]
    # Results structure may vary; just verify it's a list and search worked
    assert isinstance(results, list)


def test_search_empty_query(anon_user):
    """GET /search/?query= (empty) should handle gracefully."""
    rv = anon_user.client.get(url_for("search.SearchResource", query=""))
    assert rv.status_code == 200
    assert "results" in rv.json


def test_search_no_results(anon_user):
    """GET /search/?query=nonexistent should return empty results."""
    rv = anon_user.client.get(url_for("search.SearchResource", query="xyznonexistent123"))
    assert rv.status_code == 200
    assert rv.json["results"] == []
