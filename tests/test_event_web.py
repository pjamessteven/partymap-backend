from datetime import datetime
from flask import url_for


def test_get_event(anon_user, complete_event_factory):
    event = complete_event_factory()
    rv = anon_user.client.get(url_for("events.EventResource", event_id=event.id))
    assert rv.status_code == 200
    assert rv.json["id"] == event.id


def test_get_event_or_404(anon_user):
    rv = anon_user.client.get(
        url_for("events.EventResource", event_id="52544252-6f78-4fbd-8fb9-adb3dec7b3f8")
    )
    assert rv.status_code == 404


def test_search_events(complete_event_factory, anon_user):
    complete_event_factory(name="testing", description="one")
    complete_event_factory(name="another", description="one")
    complete_event_factory(name="blah one", description="two")

    rv = anon_user.client.get(url_for("events.EventsResource", query="one"))
    assert len(rv.json["items"]) == 3

    rv = anon_user.client.get(url_for("events.EventsResource", query="testing"))
    assert len(rv.json["items"]) == 1

    rv = anon_user.client.get(url_for("events.EventsResource", query="blah"))
    assert len(rv.json["items"]) == 1

    rv = anon_user.client.get(url_for("events.EventsResource", query="two"))
    assert len(rv.json["items"]) == 1


def test_add_event_rrule(regular_user):
    payload = {
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
    rv = regular_user.client.post(url_for("events.EventsResource"), json=payload)

    event = rv.json
    print(event)
    assert event["description"] == payload["description"]
    assert event["name"] == payload["name"]
    assert len(event["event_dates"]) == 10
    assert datetime.fromisoformat(event["event_dates"][0]["start_naive"]) == datetime(
        2021, 5, 12, 8, 00, tzinfo=None
    )
    assert datetime.fromisoformat(event["event_dates"][0]["start"]) == datetime(
        2021, 5, 11, 20, 00, tzinfo=None
    )
    assert datetime.fromisoformat(event["event_dates"][0]["end_naive"]) == datetime(
        2021, 5, 14, 20, 30, tzinfo=None
    )
    assert datetime.fromisoformat(event["event_dates"][0]["end"]) == datetime(
        2021, 5, 14, 8, 30, tzinfo=None
    )
    # check tags
    event_tags = []
    for tag in event["event_tags"]:
        event_tags.append(tag["tag"])
    for tag in payload["tags"]:
        assert tag in event_tags


def test_add_event_rrule_anon(anon_user):
    payload = {
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
    rv = anon_user.client.post(url_for("events.EventsResource"), json=payload)
    assert rv.status_code == 302  # login required


def test_update_event_rrule(complete_event_factory, regular_user):
    event = complete_event_factory(creator=regular_user)
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

    rv = regular_user.client.put(
        url_for("events.EventResource", event_id=event.id), json=payload
    )
    assert rv.status_code == 200
    event = rv.json

    assert len(event["event_dates"]) == 10

    assert datetime.fromisoformat(event["event_dates"][0]["start_naive"]) == datetime(
        2021, 5, 12, 8, 00, tzinfo=None
    )
    assert datetime.fromisoformat(event["event_dates"][0]["start"]) == datetime(
        2021, 5, 11, 20, 00, tzinfo=None
    )
    assert datetime.fromisoformat(event["event_dates"][0]["end_naive"]) == datetime(
        2021, 5, 14, 20, 30, tzinfo=None
    )
    assert datetime.fromisoformat(event["event_dates"][0]["end"]) == datetime(
        2021, 5, 14, 8, 30, tzinfo=None
    )
    assert (
        event["event_dates"][0]["location"]["description"]
        == payload["location"]["description"]
    )


def test_update_event_rrule_staff(complete_event_factory, regular_user, staff_user):
    # a staff user can update a regular users event
    event = complete_event_factory(creator=regular_user)
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

    rv = staff_user.client.put(
        url_for("events.EventResource", event_id=event.id), json=payload
    )
    assert rv.status_code == 200
    event = rv.json

    assert len(event["event_dates"]) == 10

    assert datetime.fromisoformat(event["event_dates"][0]["start_naive"]) == datetime(
        2021, 5, 12, 8, 00, tzinfo=None
    )
    assert datetime.fromisoformat(event["event_dates"][0]["start"]) == datetime(
        2021, 5, 11, 20, 00, tzinfo=None
    )
    assert datetime.fromisoformat(event["event_dates"][0]["end_naive"]) == datetime(
        2021, 5, 14, 20, 30, tzinfo=None
    )
    assert datetime.fromisoformat(event["event_dates"][0]["end"]) == datetime(
        2021, 5, 14, 8, 30, tzinfo=None
    )
    assert (
        event["event_dates"][0]["location"]["description"]
        == payload["location"]["description"]
    )


def test_update_event_no_permission(complete_event_factory, regular_user_factory):
    # a user cannot update another users event
    user1 = regular_user_factory()
    user2 = regular_user_factory()
    event = complete_event_factory(creator=user1)
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

    rv = user2.client.put(
        url_for("events.EventResource", event_id=event.id), json=payload
    )
    assert rv.status_code == 403  # no permission


def test_update_event_description(complete_event_factory, regular_user):
    event = complete_event_factory(creator=regular_user)
    payload = {"description": "updated description"}
    rv = regular_user.client.put(
        url_for("events.EventResource", event_id=event.id), json=payload
    )
    assert rv.status_code == 200  # login required
    print(rv.json)
    assert rv.json["description"] == payload["description"]


def test_update_event_url(complete_event_factory, regular_user):
    event = complete_event_factory(creator=regular_user)
    payload = {"url": "http://updatedurl.com"}
    rv = regular_user.client.put(
        url_for("events.EventResource", event_id=event.id), json=payload
    )
    assert rv.status_code == 200  # login required
    assert rv.json["default_url"] == payload["url"]


def test_update_event_tags(complete_event_factory, regular_user):
    event = complete_event_factory(creator=regular_user)
    payload = {"tags": ["test", "blah"]}

    rv = regular_user.client.put(
        url_for("events.EventResource", event_id=event.id), json=payload
    )
    assert rv.status_code == 200  # login required
    # check tags
    event_tags = []
    for tag in rv.json["event_tags"]:
        event_tags.append(tag["tag"])
    for tag in payload["tags"]:
        assert tag in event_tags


def test_delete_event(complete_event_factory, regular_user):
    event = complete_event_factory(creator=regular_user)
    event_id = event.id
    # should be retrievable
    rv = regular_user.client.get(url_for("events.EventResource", event_id=event_id))
    assert rv.status_code == 200
    # now delete it
    rv = regular_user.client.delete(url_for("events.EventResource", event_id=event_id))
    assert rv.status_code == 204
    # should 404 now that it's deleted
    rv = regular_user.client.get(url_for("events.EventResource", event_id=event_id))
    assert rv.status_code == 404


def test_delete_event_staff(complete_event_factory, regular_user, staff_user):
    event = complete_event_factory(creator=regular_user)
    event_id = event.id
    # should be retrievable
    rv = regular_user.client.get(url_for("events.EventResource", event_id=event_id))
    assert rv.status_code == 200
    # now staff user delete it
    rv = staff_user.client.delete(url_for("events.EventResource", event_id=event_id))
    assert rv.status_code == 204
    # should 404 now that it's deleted
    rv = regular_user.client.get(url_for("events.EventResource", event_id=event_id))
    assert rv.status_code == 404


def test_delete_event_no_permission(complete_event_factory, regular_user_factory):
    user1 = regular_user_factory()
    user2 = regular_user_factory()
    event = complete_event_factory(creator=user1)
    event_id = event.id
    rv = user2.client.delete(url_for("events.EventResource", event_id=event_id))
    assert rv.status_code == 403  # no permission
