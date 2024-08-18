import pytest
from datetime import datetime

import pmapi.event.controllers as events
from pmapi.event_date.model import EventDate
import pmapi.exceptions as exc
from dateutil.relativedelta import relativedelta


def test_get_event(complete_event_factory):
    event = complete_event_factory()
    result = events.get_event_or_404(event.id)
    assert result.id == event.id


def test_get_event_or_404():
    with pytest.raises(exc.RecordNotFound):
        events.get_event_or_404(2)


def test_search_events(complete_event_factory):
    complete_event_factory(name="testing", description="one")
    complete_event_factory(name="another", description="one")
    complete_event_factory(name="blah one", description="two")

    results = events.search_events(query="one")
    assert len(results.items) == 3

    results = events.search_events(query="testing")
    assert len(results.items) == 1

    results = events.search_events(query="blah")
    assert len(results.items) == 1

    results = events.search_events(query="two")
    assert len(results.items) == 1


def test_add_event_rrule(regular_user):
    payload = {
        "creator": regular_user,
        "name": "Test event",
        "description": "Test description",
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
        "dateTime": {
            "date": {
                "start": "2021-05-12T15:05:46.247Z",
                "end": "2021-05-14T15:05:46.248Z",
            },
            "startHours": 8,
            "startMinutes": "00",
            "endHours": 20,
            "endMinutes": "30",
            "allDay": False,
        },
        "rrule": {
            "recurringType": 1,
            "separationCount": 1,
            "weekOfMonth": 2,
            "dayOfMonth": 13,
            "dayOfWeek": 4,
            "monthOfYear": 5,
        },
        "url": "test.com",
        "tags": ["test1", "test2"],
        "images": None,
    }

    event = events.add_event(**payload)
    assert event.description == payload["description"]
    assert event.name == payload["name"]
    assert event.default_location.description == payload["location"]["description"]
    assert len(event.event_dates) == 10
    assert event.event_dates[0].start_naive == datetime(2021, 5, 12, 8, 00, tzinfo=None)
    assert event.event_dates[0].start == datetime(2021, 5, 11, 20, 00, tzinfo=None)
    assert event.event_dates[0].end_naive == datetime(2021, 5, 14, 20, 30, tzinfo=None)
    assert event.event_dates[0].end == datetime(2021, 5, 14, 8, 30, tzinfo=None)
    # check tags
    event_tags = []
    for tag in event.event_tags:
        event_tags.append(tag.tag.tag)
    for tag in payload["tags"]:
        assert tag in event_tags


def test_add_event_one_off_event(regular_user):
    payload = {
        "creator": regular_user,
        "name": "Test event",
        "description": "Test description",
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
        "dateTime": {
            "date": {
                "start": "2021-05-12T15:05:46.247Z",
                "end": "2021-05-14T15:05:46.248Z",
            },
            "startHours": 8,
            "startMinutes": "00",
            "endHours": 20,
            "endMinutes": "30",
            "allDay": False,
        },
        "rrule": {
            "recurringType": 1,
            "separationCount": 0,  # one off event
            "weekOfMonth": 2,
            "dayOfMonth": 13,
            "dayOfWeek": 4,
            "monthOfYear": 5,
        },
        "url": "test.com",
        "tags": ["test1", "test2"],
        "images": None,
    }

    event = events.add_event(**payload)
    assert event.description == payload["description"]
    assert event.name == payload["name"]
    assert event.default_location.description == payload["location"]["description"]
    assert len(event.event_dates) == 1
    assert event.event_dates[0].start_naive == datetime(2021, 5, 12, 8, 00, tzinfo=None)
    assert event.event_dates[0].start == datetime(2021, 5, 11, 20, 00, tzinfo=None)
    assert event.event_dates[0].end_naive == datetime(2021, 5, 14, 20, 30, tzinfo=None)
    assert event.event_dates[0].end == datetime(2021, 5, 14, 8, 30, tzinfo=None)
    # check tags
    event_tags = []
    for tag in event.event_tags:
        event_tags.append(tag.tag.tag)
    for tag in payload["tags"]:
        assert tag in event_tags


def test_update_event_rrule(complete_event_factory):
    event = complete_event_factory()
    payload = {
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
        "dateTime": {
            "date": {
                "start": "2021-05-12T15:05:46.247Z",
                "end": "2021-05-14T15:05:46.248Z",
            },
            "startHours": 8,
            "startMinutes": "00",
            "endHours": 20,
            "endMinutes": "30",
            "allDay": False,
        },
        "rrule": {
            "recurringType": 1,
            "separationCount": 1,
            "weekOfMonth": 2,
            "dayOfMonth": 13,
            "dayOfWeek": 4,
            "monthOfYear": 5,
        },
    }
    event = events.update_event(event.id, **payload)
    assert len(event.event_dates) == 10
    for ed in event.event_dates:
        print(ed.start_naive)
    assert event.event_dates[0].start_naive == datetime(2021, 5, 12, 8, 00, tzinfo=None)
    assert event.event_dates[0].start == datetime(2021, 5, 11, 20, 00, tzinfo=None)
    assert event.event_dates[0].end_naive == datetime(2021, 5, 14, 20, 30, tzinfo=None)
    assert event.event_dates[0].end == datetime(2021, 5, 14, 8, 30, tzinfo=None)
    assert event.default_location.description == payload["location"]["description"]
    assert (
        event.event_dates[0].location.description == payload["location"]["description"]
    )


def test_update_event_description(complete_event_factory):
    event = complete_event_factory()
    payload = {"description": "updated description"}
    event = events.update_event(event.id, **payload)
    assert event.description == payload["description"]


def test_update_event_url(complete_event_factory):
    event = complete_event_factory()
    payload = {"url": "updated url"}
    event = events.update_event(event.id, **payload)
    assert event.default_url == payload["url"]


def test_update_event_tags(complete_event_factory):
    event = complete_event_factory()
    payload = {"tags": ["test", "blah"]}
    event = events.update_event(event.id, **payload)
    # check tags
    event_tags = []
    for tag in event.event_tags:
        event_tags.append(tag.tag.tag)
    for tag in payload["tags"]:
        assert tag in event_tags


def test_delete_event(complete_event_factory):
    event = complete_event_factory()
    id = event.id
    events.delete_event(id)
    with pytest.raises(exc.RecordNotFound):
        events.get_event_or_404(id)
