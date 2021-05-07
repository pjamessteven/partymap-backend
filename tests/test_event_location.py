import pytest
from datetime import datetime, timedelta

import pmapi.event_location.controllers as event_locations
from pmapi.event_location.model import EventLocationType
from pmapi.exceptions import RecordAlreadyExists
from pmapi.exceptions import RecordNotFound


def test_add_location(regular_user):
    location_data = {
        "geometry": {"location": {"lat": -41.285296, "lng": 174.771275}},
        "name": "test location",
        "description": "test description",
        "place_id": "12345678",
        "types": ["restaurant", "cafe"],
        "address_components": [
            {
                "long_name": "Barcelona",
                "short_name": "Barcelona",
                "types": ["locality", "political"],
            },
            {
                "long_name": "Barcelona",
                "short_name": "B",
                "types": ["administrative_area_level_2", "political"],
            },
            {
                "long_name": "Catalonia",
                "short_name": "CT",
                "types": ["administrative_area_level_1", "political"],
            },
            {
                "long_name": "Spain",
                "short_name": "ES",
                "types": ["country", "political"],
            },
        ],
    }

    location = event_locations.add_new_event_location(
        creator=regular_user, **location_data
    )
    # test get location while we're at it
    location = event_locations.get_location(location_data["place_id"])
    assert location.name == location_data["name"]
    assert location.description == location_data["description"]
    assert location.place_id == location_data["place_id"]
    assert location.name == location_data["name"]
    assert location.lat == location_data["geometry"]["location"]["lat"]
    assert location.lng == location_data["geometry"]["location"]["lng"]
    assert location.city == "Wellington"
    assert location.country == "New Zealand"
    assert location.country_code == "NZ"
    assert location.address_components == location_data["address_components"]


def test_add_dupliacte_location(regular_user):
    location_data = {
        "geometry": {"location": {"lat": -41.285296, "lng": 174.771275}},
        "name": "test location",
        "description": "test description",
        "place_id": "12345678",
        "types": ["restaurant", "cafe"],
    }

    event_locations.add_new_event_location(creator=regular_user, **location_data)

    with pytest.raises(RecordAlreadyExists):
        event_locations.add_new_event_location(creator=regular_user, **location_data)


def test_add_event_location_types(regular_user, db):
    location_data = {
        "geometry": {"location": {"lat": -41.285296, "lng": 174.771275}},
        "name": "test location",
        "description": "test description",
        "place_id": "12345678",
        "types": ["restaurant", "cafe"],
    }

    event_locations.add_new_event_location(creator=regular_user, **location_data)
    location_types = db.session.query(EventLocationType).all()
    assert len(location_types) == len(location_data["types"])
    for t in location_types:
        assert t.type in location_data["types"]


def test_add_multiple_of_same_location_types(regular_user, db):
    location_data = {
        "geometry": {"location": {"lat": -41.285296, "lng": 174.771275}},
        "name": "test location",
        "description": "test description",
        "place_id": "12345678",
        "types": ["restaurant", "cafe", "cafe"],
    }

    event_location = event_locations.add_new_event_location(
        creator=regular_user, **location_data
    )
    location_types = db.session.query(EventLocationType).all()
    # check event_location object has two types
    assert len(event_location.types) == 2
    # check theres only two types in the db
    assert len(location_types) == 2


def test_get_event_location_or_404(regular_user):
    location_data = {
        "geometry": {"location": {"lat": -41.285296, "lng": 174.771275}},
        "name": "test location",
        "description": "test description",
        "place_id": "12345678",
        "types": ["restaurant", "cafe"],
    }

    event_location = event_locations.add_new_event_location(
        creator=regular_user, **location_data
    )
    assert (
        event_location.place_id
        == event_locations.get_location_or_404(event_location.place_id).place_id
    )


def test_get_event_location_or_404_error():
    with pytest.raises(RecordNotFound):
        event_locations.get_location_or_404("testing")


def test_get_all_locations(regular_user, event_date_factory):
    event_date_factory(
        start=datetime(year=2006, month=1, day=1),
        end=datetime(year=2006, month=1, day=5),
    )
    locations = event_locations.get_all_locations()
    assert len(locations.all()) == 1


def test_get_all_locations_dates(regular_user, event_date_factory):
    start = datetime(year=2006, month=1, day=1)
    end = datetime(year=2006, month=1, day=5)
    event_date_factory(start, end)
    locations = event_locations.get_all_locations(date_min=start, date_max=end)
    assert len(locations.all()) == 1


def test_get_all_locations_dates_out_of_ranges(regular_user, event_date_factory):
    start = datetime(year=2006, month=1, day=1)
    end = datetime(year=2006, month=1, day=5)
    event_date_factory(start, end)
    locations = event_locations.get_all_locations(
        date_min=start + timedelta(hours=1), date_max=end
    )
    assert len(locations.all()) == 0


def test_get_all_locations_dates_out_of_ranges_2(regular_user, event_date_factory):
    start = datetime(year=2006, month=1, day=1)
    event_date_factory(start)
    locations = event_locations.get_all_locations(date_min=start + timedelta(hours=1))
    assert len(locations.all()) == 0


def test_get_all_locations_tag_search(db, regular_user, complete_event_factory):
    start = datetime(year=2006, month=1, day=1)
    complete_event_factory(start=start, tags=["test1"])
    locations = event_locations.get_all_locations(tags=["test1"])
    print(locations.all())
    assert len(locations.all()) == 1


def test_get_all_locations_tag_search_multiple(
    db, regular_user, complete_event_factory
):
    start = datetime(year=2006, month=1, day=1)
    complete_event_factory(start=start, tags=["test1", "test3"])
    complete_event_factory(start=start, tags=["test1", "test2"])
    locations = event_locations.get_all_locations(tags=["test1"])
    assert len(locations.all()) == 2
    locations = event_locations.get_all_locations(tags=["test2"])
    assert len(locations.all()) == 1


def test_get_all_locations_tag_search_multiple_2(
    db, regular_user, complete_event_factory
):
    start = datetime(year=2006, month=1, day=1)
    complete_event_factory(start=start, tags=["test1", "test3"])
    complete_event_factory(start=start, tags=["test1", "test2"])
    locations = event_locations.get_all_locations(tags=["test1", "test3"])
    assert len(locations.all()) == 1
