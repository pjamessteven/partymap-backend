from datetime import datetime
from flask import url_for
import json
from dateutil.relativedelta import relativedelta
from pmapi.event_date.model import EventDate


def test_add_event_date_with_datetime(regular_user, complete_event_factory):
    event = complete_event_factory()

    payload = {
        "event_id": event.id,
        "dateTime": {
            "date": {
                "start": "2021-04-08T02:00:00.000Z",
                "end": "2021-04-08T04:00:00.000Z",
            },
            "startHours": 9,
            "startMinutes": 15,
            "endHours": 10,
            "endMinutes": 30,
            "allDay": False,
        },
        "location": {
            "address_components": [
                {
                    "long_name": "Timaru",
                    "short_name": "Timaru",
                    "types": ["locality", "political"],
                },
                {
                    "long_name": "Canterbury",
                    "short_name": "Canterbury",
                    "types": ["administrative_area_level_1", "political"],
                },
                {
                    "long_name": "New Zealand",
                    "short_name": "NZ",
                    "types": ["country", "political"],
                },
            ],
            "geometry": {
                "location": {"lat": -44.3903881, "lng": 171.2372756},
                "viewport": {
                    "south": -44.42603005279609,
                    "west": 171.1740580162034,
                    "north": -44.33174896335244,
                    "east": 171.272916966389,
                },
            },
            "name": "Timaru",
            "types": ["locality", "political"],
            "html_attributions": [],
            "description": "Timaru, New Zealand",
            "place_id": "ChIJ78dhY4ljLG0ROZl5hIbvAAU",
        },
        "description": "Test description",
        "url": "https://www.test.com",
    }

    rv = regular_user.client.post(
        url_for("dates.EventDatesResource", event_id=event.id), json=payload
    )
    assert regular_user.id == event.creator_id  # only the event creator can add dates
    assert rv.status_code == 200
    assert rv.json["event_id"] == event.id
    assert rv.json["description"] == "Test description"
    assert rv.json["url"] == "https://www.test.com"
    assert rv.json["tz"] == "Pacific/Auckland"
    assert rv.json["location"]["city"] == "Timaru"  # test that geocode is working
    assert rv.json["location"]["country_code"] == "NZ"
    assert rv.json["location"]["country"] == "New Zealand"
    assert rv.json["location"]["description"] == "Timaru, New Zealand"
    assert datetime.fromisoformat(rv.json["start"]) == datetime(
        2021, 4, 7, 21, 15, 0, 0, tzinfo=None
    )
    assert datetime.fromisoformat(rv.json["start_naive"]) == datetime(
        2021, 4, 8, 9, 15, 0, 0, tzinfo=None
    )
    assert datetime.fromisoformat(rv.json["end"]) == datetime(
        2021, 4, 7, 22, 30, 0, 0, tzinfo=None
    )
    assert datetime.fromisoformat(rv.json["end_naive"]) == datetime(
        2021, 4, 8, 10, 30, 0, 0, tzinfo=None
    )


def test_add_event_date_with_datetime_staff(
    regular_user, staff_user, complete_event_factory
):
    event = complete_event_factory(creator=regular_user)
    assert regular_user.id == event.creator_id

    payload = {
        "event_id": event.id,
        "dateTime": {
            "date": {
                "start": "2021-04-08T02:00:00.000Z",
                "end": "2021-04-08T04:00:00.000Z",
            },
            "startHours": 9,
            "startMinutes": 15,
            "endHours": 10,
            "endMinutes": 30,
            "allDay": False,
        },
        "location": {
            "address_components": [
                {
                    "long_name": "Timaru",
                    "short_name": "Timaru",
                    "types": ["locality", "political"],
                },
                {
                    "long_name": "Canterbury",
                    "short_name": "Canterbury",
                    "types": ["administrative_area_level_1", "political"],
                },
                {
                    "long_name": "New Zealand",
                    "short_name": "NZ",
                    "types": ["country", "political"],
                },
            ],
            "geometry": {
                "location": {"lat": -44.3903881, "lng": 171.2372756},
                "viewport": {
                    "south": -44.42603005279609,
                    "west": 171.1740580162034,
                    "north": -44.33174896335244,
                    "east": 171.272916966389,
                },
            },
            "name": "Timaru",
            "types": ["locality", "political"],
            "html_attributions": [],
            "description": "Timaru, New Zealand",
            "place_id": "ChIJ78dhY4ljLG0ROZl5hIbvAAU",
        },
        "description": "Test description",
        "url": "https://www.test.com",
    }

    rv = staff_user.client.post(
        url_for("dates.EventDatesResource", event_id=event.id), json=payload
    )
    assert rv.status_code == 200


def test_add_event_date_with_datetime_admin(
    regular_user, admin_user, complete_event_factory
):
    event = complete_event_factory(creator=regular_user)
    assert regular_user.id == event.creator_id

    payload = {
        "event_id": event.id,
        "dateTime": {
            "date": {
                "start": "2021-04-08T02:00:00.000Z",
                "end": "2021-04-08T04:00:00.000Z",
            },
            "startHours": 9,
            "startMinutes": 15,
            "endHours": 10,
            "endMinutes": 30,
            "allDay": False,
        },
        "location": {
            "address_components": [
                {
                    "long_name": "Timaru",
                    "short_name": "Timaru",
                    "types": ["locality", "political"],
                },
                {
                    "long_name": "Canterbury",
                    "short_name": "Canterbury",
                    "types": ["administrative_area_level_1", "political"],
                },
                {
                    "long_name": "New Zealand",
                    "short_name": "NZ",
                    "types": ["country", "political"],
                },
            ],
            "geometry": {
                "location": {"lat": -44.3903881, "lng": 171.2372756},
                "viewport": {
                    "south": -44.42603005279609,
                    "west": 171.1740580162034,
                    "north": -44.33174896335244,
                    "east": 171.272916966389,
                },
            },
            "name": "Timaru",
            "types": ["locality", "political"],
            "html_attributions": [],
            "description": "Timaru, New Zealand",
            "place_id": "ChIJ78dhY4ljLG0ROZl5hIbvAAU",
        },
        "description": "Test description",
        "url": "https://www.test.com",
    }

    rv = admin_user.client.post(
        url_for("dates.EventDatesResource", event_id=event.id), json=payload
    )
    assert rv.status_code == 200


def test_add_event_date_with_datetime_unpriviliged(
    regular_user, regular_user_factory, complete_event_factory
):
    event = complete_event_factory(creator=regular_user)
    assert regular_user.id == event.creator_id

    regular_user_2 = regular_user_factory()

    payload = {
        "event_id": event.id,
        "dateTime": {
            "date": {
                "start": "2021-04-08T02:00:00.000Z",
                "end": "2021-04-08T04:00:00.000Z",
            },
            "startHours": 9,
            "startMinutes": 15,
            "endHours": 10,
            "endMinutes": 30,
            "allDay": False,
        },
        "location": {
            "address_components": [
                {
                    "long_name": "Timaru",
                    "short_name": "Timaru",
                    "types": ["locality", "political"],
                },
                {
                    "long_name": "Canterbury",
                    "short_name": "Canterbury",
                    "types": ["administrative_area_level_1", "political"],
                },
                {
                    "long_name": "New Zealand",
                    "short_name": "NZ",
                    "types": ["country", "political"],
                },
            ],
            "geometry": {
                "location": {"lat": -44.3903881, "lng": 171.2372756},
                "viewport": {
                    "south": -44.42603005279609,
                    "west": 171.1740580162034,
                    "north": -44.33174896335244,
                    "east": 171.272916966389,
                },
            },
            "name": "Timaru",
            "types": ["locality", "political"],
            "html_attributions": [],
            "description": "Timaru, New Zealand",
            "place_id": "ChIJ78dhY4ljLG0ROZl5hIbvAAU",
        },
        "description": "Test description",
        "url": "https://www.test.com",
    }

    rv = regular_user_2.client.post(
        url_for("dates.EventDatesResource", event_id=event.id), json=payload
    )
    assert rv.status_code == 403  # invalid permissions


def test_update_event(regular_user, event_date_factory):
    event_date = event_date_factory()
    payload = {
        "dateTime": {
            "date": {
                "start": "2021-04-08T02:00:00.000Z",
                "end": "2021-04-08T04:00:00.000Z",
            },
            "startHours": 9,
            "startMinutes": 15,
            "endHours": 10,
            "endMinutes": 30,
            "allDay": False,
        },
        "cancelled": True,
        "url": "test12.com",
        "description": "Updated description",
        "location": {
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
            "geometry": {
                "location": {"lat": 41.3850639, "lng": 2.1734035},
                "viewport": {
                    "south": 41.32000404256846,
                    "west": 2.069525775337128,
                    "north": 41.46957607668864,
                    "east": 2.228009940794638,
                },
            },
            "name": "Barcelona",
            "types": ["locality", "political"],
            "html_attributions": [],
            "description": "Barcelona, Spain",
            "place_id": "ChIJ5TCOcRaYpBIRCmZHTz37sEQ",
        },
    }

    rv = regular_user.client.put(
        url_for("dates.DateResource", id=event_date.id), json=payload
    )
    assert rv.status_code == 200
    assert rv.json["description"] == "Updated description"
    assert rv.json["url"] == "test12.com"
    assert rv.json["tz"] == "Europe/Madrid"
    assert rv.json["location"]["city"] == "Barri Gòtic"  # test that geocode is working
    assert rv.json["location"]["country_code"] == "ES"  # test that geocode is working
    assert rv.json["location"]["country"] == "Spain"  # test that geocode is working
    assert rv.json["location"]["description"] == "Barcelona, Spain"
    assert rv.json["cancelled"] is True

    assert datetime.fromisoformat(rv.json["start"]) == datetime(
        2021, 4, 8, 7, 15, tzinfo=None
    )
    assert datetime.fromisoformat(rv.json["start_naive"]) == datetime(
        2021, 4, 8, 9, 15, tzinfo=None
    )
    assert datetime.fromisoformat(rv.json["end"]) == datetime(
        2021, 4, 8, 8, 30, tzinfo=None
    )
    assert datetime.fromisoformat(rv.json["end_naive"]) == datetime(
        2021, 4, 8, 10, 30, tzinfo=None
    )


def test_update_event_staff(regular_user, staff_user, event_date_factory):
    event_date = event_date_factory()
    assert regular_user.id == event_date.creator_id

    payload = {
        "dateTime": {
            "date": {
                "start": "2021-04-08T02:00:00.000Z",
                "end": "2021-04-08T04:00:00.000Z",
            },
            "startHours": 9,
            "startMinutes": 15,
            "endHours": 10,
            "endMinutes": 30,
            "allDay": False,
        },
        "cancelled": True,
        "url": "test12.com",
        "description": "Updated description",
        "location": {
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
            "geometry": {
                "location": {"lat": 41.3850639, "lng": 2.1734035},
                "viewport": {
                    "south": 41.32000404256846,
                    "west": 2.069525775337128,
                    "north": 41.46957607668864,
                    "east": 2.228009940794638,
                },
            },
            "name": "Barcelona",
            "types": ["locality", "political"],
            "html_attributions": [],
            "description": "Barcelona, Spain",
            "place_id": "ChIJ5TCOcRaYpBIRCmZHTz37sEQ",
        },
    }

    rv = staff_user.client.put(
        url_for("dates.DateResource", id=event_date.id), json=payload
    )
    assert rv.status_code == 200


def test_update_event_admin(regular_user, admin_user, event_date_factory):
    event_date = event_date_factory()
    assert regular_user.id == event_date.creator_id

    payload = {
        "dateTime": {
            "date": {
                "start": "2021-04-08T02:00:00.000Z",
                "end": "2021-04-08T04:00:00.000Z",
            },
            "startHours": 9,
            "startMinutes": 15,
            "endHours": 10,
            "endMinutes": 30,
            "allDay": False,
        },
        "cancelled": True,
        "url": "test12.com",
        "description": "Updated description",
        "location": {
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
            "geometry": {
                "location": {"lat": 41.3850639, "lng": 2.1734035},
                "viewport": {
                    "south": 41.32000404256846,
                    "west": 2.069525775337128,
                    "north": 41.46957607668864,
                    "east": 2.228009940794638,
                },
            },
            "name": "Barcelona",
            "types": ["locality", "political"],
            "html_attributions": [],
            "description": "Barcelona, Spain",
            "place_id": "ChIJ5TCOcRaYpBIRCmZHTz37sEQ",
        },
    }

    rv = admin_user.client.put(
        url_for("dates.DateResource", id=event_date.id), json=payload
    )
    assert rv.status_code == 200


def test_update_event_unpriviliged(
    regular_user, regular_user_factory, event_date_factory
):
    event_date = event_date_factory()
    assert regular_user.id == event_date.creator_id

    regular_user_2 = regular_user_factory()

    payload = {
        "dateTime": {
            "date": {
                "start": "2021-04-08T02:00:00.000Z",
                "end": "2021-04-08T04:00:00.000Z",
            },
            "startHours": 9,
            "startMinutes": 15,
            "endHours": 10,
            "endMinutes": 30,
            "allDay": False,
        },
        "cancelled": True,
        "url": "test12.com",
        "description": "Updated description",
        "location": {
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
            "geometry": {
                "location": {"lat": 41.3850639, "lng": 2.1734035},
                "viewport": {
                    "south": 41.32000404256846,
                    "west": 2.069525775337128,
                    "north": 41.46957607668864,
                    "east": 2.228009940794638,
                },
            },
            "name": "Barcelona",
            "types": ["locality", "political"],
            "html_attributions": [],
            "description": "Barcelona, Spain",
            "place_id": "ChIJ5TCOcRaYpBIRCmZHTz37sEQ",
        },
    }

    rv = regular_user_2.client.put(
        url_for("dates.DateResource", id=event_date.id), json=payload
    )
    assert rv.status_code == 403


def test_delete_event_date(regular_user, event_date_factory):
    event_date = event_date_factory()
    assert regular_user.id == event_date.creator_id

    rv = regular_user.client.delete(url_for("dates.DateResource", id=event_date.id))
    assert rv.status_code == 204


def test_delete_event_date_staff(regular_user, staff_user, event_date_factory):
    event_date = event_date_factory()
    assert regular_user.id == event_date.creator_id

    rv = staff_user.client.delete(url_for("dates.DateResource", id=event_date.id))
    assert rv.status_code == 204


def test_delete_event_date_admin(regular_user, admin_user, event_date_factory):
    event_date = event_date_factory()
    assert regular_user.id == event_date.creator_id

    rv = admin_user.client.delete(url_for("dates.DateResource", id=event_date.id))
    assert rv.status_code == 204


def test_delete_event_date_unpriviliged(
    regular_user, regular_user_factory, event_date_factory
):
    event_date = event_date_factory()
    assert regular_user.id == event_date.creator_id

    regular_user_2 = regular_user_factory()

    rv = regular_user_2.client.delete(url_for("dates.DateResource", id=event_date.id))
    assert rv.status_code == 403


def test_query_event_dates_bounds_tags_dates(
    anon_user,
    regular_user,
    admin_user,
    complete_event_factory,
    event_location_factory,
    first_saturday_of_next_month_at_1330pm,
    db,
):

    # roughly timaru
    location1 = event_location_factory(
        name="timaru", geometry={"location": {"lat": -44.386692, "lng": 171.562500}}
    )

    # roughly barcelona
    location2 = event_location_factory(
        name="barcelona", geometry={"location": {"lat": 41.426253, "lng": 1.933594}}
    )

    # tomorrow
    tomorrow = datetime.now() + relativedelta(day=1)
    day_after_tomorrow = datetime.now() + relativedelta(day=2)

    complete_event_factory(
        event_location=location1,
        start=first_saturday_of_next_month_at_1330pm(),
        tags=["test", "timaru"],
        creator=admin_user,
    )

    complete_event_factory(
        event_location=location2,
        start=tomorrow,
        end=day_after_tomorrow,
        tags=["test", "barca"],
        creator=regular_user,
    )

    assert db.session.query(EventDate).count() == 2

    # rougly the area of nz
    bounds = {
        "_northEast": {"lat": 2.0210651187669897, "lng": 247.23632812500003},
        "_southWest": {"lat": -61.85614879566797, "lng": 130.34179687500003},
    }
    bounds = json.dumps(bounds)

    # inauthenticated user can query
    rv = anon_user.client.get(
        url_for(
            "dates.DatesResource",
            date_min=first_saturday_of_next_month_at_1330pm(),
            date_max=first_saturday_of_next_month_at_1330pm() + relativedelta(days=1),
            bounds=bounds,
            tags=["timaru"],
        )
    )
    assert len(rv.json["items"]) == 1

    # inauthenticated user can query
    # test non-existent tag
    rv = anon_user.client.get(
        url_for(
            "dates.DatesResource",
            date_min=first_saturday_of_next_month_at_1330pm(),
            date_max=first_saturday_of_next_month_at_1330pm() + relativedelta(days=1),
            bounds=bounds,
            tags=["nothing"],
        )
    )
    assert len(rv.json["items"]) == 0

    # test out of bounds
    bounds = {  # roughly the area around new york
        "_northEast": {"lat": 46.255847, "lng": -413.569336},
        "_southWest": {"lat": 30.429730, "lng": -450.483398},
    }
    bounds = json.dumps(bounds)

    rv = anon_user.client.get(
        url_for(
            "dates.DatesResource",
            bounds=bounds,
        )
    )
    assert len(rv.json["items"]) == 0

    # test get all
    rv = anon_user.client.get(
        url_for(
            "dates.DatesResource",
        )
    )
    assert len(rv.json["items"]) == 2


def test_query_single_event_date(complete_event_factory, anon_user):
    event = complete_event_factory()
    # 1 event date should have been created
    assert len(event.event_dates) == 1

    rv = anon_user.client.get(url_for("dates.DateResource", id=event.event_dates[0].id))
    assert rv.json["id"] == event.event_dates[0].id
