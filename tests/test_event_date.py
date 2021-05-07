import pytest
from datetime import datetime

import pmapi.event_date.controllers as event_dates
import pmapi.exceptions as exc


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

    event_date = event_dates.add_event_date_with_datetime(**payload)

    assert event_date.event_id == event.id
    assert event_date.description == "Test description"
    assert event_date.url == "https://www.test.com"
    assert event_date.tz == "Pacific/Auckland"
    assert event_date.location.city == "Timaru"  # test that geocode is working
    assert event_date.location.country_code == "NZ"  # test that geocode is working
    assert event_date.location.country == "New Zealand"  # test that geocode is working
    assert event_date.location.description == "Timaru, New Zealand"
    assert event_date.start == datetime(2021, 4, 7, 21, 15, 0, 0, tzinfo=None)
    assert event_date.start_naive == datetime(2021, 4, 8, 9, 15, 0, 0, tzinfo=None)
    assert event_date.end == datetime(2021, 4, 7, 22, 30, 0, 0, tzinfo=None)
    assert event_date.end_naive == datetime(2021, 4, 8, 10, 30, 0, 0, tzinfo=None)


def test_add_event_date_with_datetime_end_before_start(
    regular_user, complete_event_factory
):
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
            "endHours": 8,
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

    with pytest.raises(exc.InvalidAPIRequest):
        event_dates.add_event_date_with_datetime(**payload)


def test_add_event_date(regular_user, complete_event_factory):
    event = complete_event_factory()

    payload = {
        "event": event,
        "start_naive": datetime(2021, 4, 8, 9, 15, 0, 0, tzinfo=None),
        "end_naive": datetime(2021, 4, 8, 10, 30, 0, 0, tzinfo=None),
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

    event_date = event_dates.add_event_date(**payload)

    assert event_date.event_id == event.id
    assert event_date.description == "Test description"
    assert event_date.url == "https://www.test.com"
    assert event_date.tz == "Pacific/Auckland"
    assert event_date.location.city == "Timaru"  # test that geocode is working
    assert event_date.location.country_code == "NZ"  # test that geocode is working
    assert event_date.location.country == "New Zealand"  # test that geocode is working
    assert event_date.location.description == "Timaru, New Zealand"
    assert event_date.start == datetime(2021, 4, 7, 21, 15, 0, 0, tzinfo=None)
    assert event_date.start_naive == datetime(2021, 4, 8, 9, 15, 0, 0, tzinfo=None)
    assert event_date.end == datetime(2021, 4, 7, 22, 30, 0, 0, tzinfo=None)
    assert event_date.end_naive == datetime(2021, 4, 8, 10, 30, 0, 0, tzinfo=None)


def test_add_event_date_no_location(regular_user, complete_event_factory):
    event = complete_event_factory()

    payload = {
        "event": event,
        "start_naive": datetime(2021, 4, 8, 9, 15, 0, 0, tzinfo=None),
        "end_naive": datetime(2021, 4, 8, 10, 30, 0, 0, tzinfo=None),
        "description": "Test description",
        "url": "https://www.test.com",
    }

    with pytest.raises(exc.InvalidAPIRequest):
        event_dates.add_event_date(**payload)


def test_add_event_date_end_before_start(regular_user, complete_event_factory):
    event = complete_event_factory()

    payload = {
        "event": event,
        "end_naive": datetime(2021, 4, 8, 10, 30, 0, 0, tzinfo=None),
        "start_naive": datetime(2021, 4, 8, 9, 15, 0, 0, tzinfo=None),
        "description": "Test description",
        "url": "https://www.test.com",
    }

    with pytest.raises(exc.InvalidAPIRequest):
        event_dates.add_event_date(**payload)


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

    event_date = event_dates.update_event_date(event_date.id, **payload)

    assert event_date.description == "Updated description"
    assert event_date.url == "test12.com"
    assert event_date.tz == "Europe/Madrid"
    assert event_date.location.city == "Barri Gòtic"  # test that geocode is working
    assert event_date.location.country_code == "ES"  # test that geocode is working
    assert event_date.location.country == "Spain"  # test that geocode is working
    assert event_date.location.description == "Barcelona, Spain"
    assert (
        event_date.location.address_components
        == payload["location"]["address_components"]
    )
    assert event_date.start == datetime(2021, 4, 8, 7, 15, tzinfo=None)
    assert event_date.start_naive == datetime(2021, 4, 8, 9, 15, tzinfo=None)
    assert event_date.end == datetime(2021, 4, 8, 8, 30, tzinfo=None)
    assert event_date.end_naive == datetime(2021, 4, 8, 10, 30, tzinfo=None)
    assert event_date.cancelled is True


def test_update_event_end_before_start(regular_user, event_date_factory):
    event_date = event_date_factory()
    payload = {
        "dateTime": {
            "date": {
                "end": "2021-04-08T02:00:00.000Z",
                "start": "2021-04-08T04:00:00.000Z",
            },
            "startHours": 9,
            "startMinutes": 15,
            "endHours": 8,
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

    with pytest.raises(exc.InvalidAPIRequest):
        event_date = event_dates.update_event_date(event_date.id, **payload)


def test_generate_future_event_dates_for_event(
    regular_user, complete_event_factory, rrule_factory
):
    event = complete_event_factory()
    # event should have one event date by default
    print(event.event_dates)
    print(event.event_dates[0].start)
    assert len(event.future_event_dates()) == 1
    rrule = {  # every month on the 1st day
        "recurring_type": 2,
        "separation_count": 1,
        "day_of_week": 4,
        "week_of_month": None,
        "day_of_month": 1,
        "month_of_year": 5,
    }
    rrule = rrule_factory(event, rrule)
    event_dates.generate_future_event_dates(event, rrule=rrule)
    assert len(event.future_event_dates()) == 10
