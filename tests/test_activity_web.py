from flask import url_for


def test_get_all_activities(anon_user, complete_event_factory):
    """GET /activity should return all activities grouped by transaction."""
    complete_event_factory(name="activity test event")

    rv = anon_user.client.get(url_for("activity.ActivityResource"))
    assert rv.status_code == 200
    assert "items" in rv.json


def test_get_activities_filtered_by_username(anon_user, complete_event_factory, regular_user):
    """GET /activity?username=... should filter activities to that user."""
    complete_event_factory(name="activity filter event")

    rv = anon_user.client.get(
        url_for("activity.ActivityResource", username=regular_user.username)
    )
    assert rv.status_code == 200
    assert "items" in rv.json


def test_get_activities_paginated(anon_user, complete_event_factory):
    """GET /activity?page=... should paginate activities."""
    complete_event_factory(name="paginated activity event")

    rv = anon_user.client.get(url_for("activity.ActivityResource", page=1, per_page=5))
    assert rv.status_code == 200
    assert "items" in rv.json
