from datetime import datetime
from flask import url_for


def test_get_locations(anon_user, event_location_factory):
    event_location_factory()
    event_location_factory()
    rv = anon_user.client.get(url_for("locations.LocationsResource"))
    print(rv.json)
    assert len(rv.json["items"]) == 2


def test_get_locations_date_range(anon_user, complete_event_factory):
    complete_event_factory(start=datetime(year=2006, month=1, day=1))
    rv = anon_user.client.get(
        url_for(
            "locations.LocationsResource", date_min=datetime(year=2006, month=1, day=1)
        )
    )
    assert len(rv.json["items"]) == 1


def test_get_locations_tags(anon_user, complete_event_factory):
    complete_event_factory(tags=["test1", "test2"])
    complete_event_factory(tags=["test1", "test2"])
    complete_event_factory(tags=["test3", "test2"])
    rv = anon_user.client.get(url_for("locations.LocationsResource", tags=["test1"]))
    assert len(rv.json["items"]) == 2


def test_get_locations_date_rage_tags(anon_user, complete_event_factory):
    complete_event_factory(
        tags=["test1", "test2"], start=datetime(year=2010, month=1, day=1)
    )
    complete_event_factory(
        tags=["test1", "test2"], start=datetime(year=2006, month=1, day=1)
    )
    complete_event_factory(
        tags=["test3", "test2"], start=datetime(year=2006, month=1, day=1)
    )
    rv = anon_user.client.get(
        url_for(
            "locations.LocationsResource",
            tags=["test1"],
            date_min=datetime(year=2010, month=1, day=1),
        )
    )
    assert len(rv.json["items"]) == 1


def test_get_points(anon_user, event_location_factory):
    event_location_factory()
    event_location_factory()

    rv = anon_user.client.get(url_for("locations.PointsResource"))
    assert len(rv.json) == 2


def test_get_points_date_range(anon_user, complete_event_factory):
    complete_event_factory(start=datetime(year=2006, month=1, day=1))
    rv = anon_user.client.get(
        url_for(
            "locations.PointsResource", date_min=datetime(year=2006, month=1, day=1)
        )
    )
    assert len(rv.json) == 1


def test_get_points_tags(anon_user, complete_event_factory):
    complete_event_factory(tags=["test1", "test2"])
    complete_event_factory(tags=["test1", "test2"])
    complete_event_factory(tags=["test3", "test2"])
    rv = anon_user.client.get(url_for("locations.PointsResource", tags=["test1"]))
    assert len(rv.json) == 2


def test_get_points_date_range_tags(anon_user, complete_event_factory):
    complete_event_factory(
        tags=["test1", "test2"], start=datetime(year=2010, month=1, day=1)
    )
    complete_event_factory(
        tags=["test1", "test2"], start=datetime(year=2006, month=1, day=1)
    )
    complete_event_factory(
        tags=["test3", "test2"], start=datetime(year=2006, month=1, day=1)
    )
    rv = anon_user.client.get(
        url_for(
            "locations.PointsResource",
            tags=["test1"],
            date_min=datetime(year=2010, month=1, day=1),
        )
    )
    assert len(rv.json) == 1


def test_get_event_location_or_404(anon_user, event_location_factory):
    event_location = event_location_factory()
    rv = anon_user.client.get(
        url_for(
            "locations.LocationResource",
            place_id=event_location.place_id,
        )
    )
    assert rv.status_code == 200
    assert rv.json["place_id"] == event_location.place_id


def test_get_event_location_or_404_error(anon_user):
    rv = anon_user.client.get(
        url_for(
            "locations.LocationResource",
            place_id="test1",
        )
    )
    assert rv.status_code == 404
