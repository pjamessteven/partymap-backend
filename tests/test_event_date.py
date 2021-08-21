import pytest
from datetime import datetime

import pmapi.event_date.controllers as event_dates
from pmapi.event_date.model import EventDate
import pmapi.exceptions as exc
from dateutil.relativedelta import relativedelta


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
    assert len(event.future_event_dates) == 1
    rrule = {  # every month on the 1st day
        "recurring_type": 2,
        "separation_count": 1,
        "day_of_week": 4,
        "week_of_month": None,
        "day_of_month": 1,
        # "month_of_year": 5, unused
    }
    rrule = rrule_factory(event, rrule)
    event_dates.generate_future_event_dates(event, rrule=rrule)
    for index, ed in enumerate(event.event_dates):
        if index == 0:
            pass
        else:
            # there should be a month between each event_date
            next_date = event.event_dates[index - 1].start + relativedelta(months=1)
            assert ed.start.month == next_date.month

    assert len(event.future_event_dates) == 10


def test_generate_future_event_dates_for_event_partial_monthly(
    regular_user, complete_event_factory, rrule_factory, db
):
    event = complete_event_factory()
    # event should have one event date by default

    assert len(event.future_event_dates) == 1
    rrule = {  # every month on the 1st day
        "recurring_type": 2,
        "separation_count": 1,
        "day_of_week": 4,
        "week_of_month": None,
        "day_of_month": 1,
        # "month_of_year": 5, unused
    }
    rrule = rrule_factory(event, rrule)
    event_dates.generate_future_event_dates(event, rrule=rrule)
    for event_date in event.event_dates[5:]:
        db.session.delete(event_date)
    db.session.commit()
    assert len(event.event_dates) == 5
    event_dates.generate_future_event_dates(event, rrule=rrule)
    for index, ed in enumerate(event.event_dates):
        if index == 0:
            pass
        else:
            # there should be a month between each event_date
            next_expected_date = event.event_dates[index - 1].start + relativedelta(
                months=1
            )
            assert ed.start.month == next_expected_date.month

    assert len(event.future_event_dates) == 10


def test_generate_future_event_dates_for_event_partial_weekly(
    regular_user, complete_event_factory, rrule_factory, db
):
    event = complete_event_factory()
    # event should have one event date by default
    assert len(event.future_event_dates) == 1
    rrule = {  # every week
        "recurring_type": 1,  # weekly recurring type
        "separation_count": 1,
        "day_of_week": 4,
        "week_of_month": 1,
        "day_of_month": 1,
        # "month_of_year": 5, unused
    }
    rrule = rrule_factory(event, rrule)
    event_dates.generate_future_event_dates(event, rrule=rrule)
    # delete five most recent dates
    for event_date in event.event_dates[5:]:
        db.session.delete(event_date)
    db.session.commit()
    assert len(event.event_dates) == 5
    event_dates.generate_future_event_dates(event, rrule=rrule)
    future_event_dates = event.future_event_dates
    for index, ed in enumerate(future_event_dates):
        if index == 0:
            pass
        else:
            # there should be a month between each event_date
            next_expected_date = future_event_dates[index - 1].start + relativedelta(
                weeks=1
            )
            assert ed.start.day == next_expected_date.day

    assert len(event.future_event_dates) == 10


def test_generate_future_event_dates_for_event_partial_yearly(
    regular_user, complete_event_factory, rrule_factory, db
):
    event = complete_event_factory()
    # event should have one event date by default
    assert len(event.future_event_dates) == 1
    rrule = {  # every year on the 1st day
        "recurring_type": 3,  # yearly recurring type
        "separation_count": 1,
        "day_of_week": 4,
        "week_of_month": 1,
        "day_of_month": 1,
        # "month_of_year": 5, unused
    }
    rrule = rrule_factory(event, rrule)
    event_dates.generate_future_event_dates(event, rrule=rrule)
    # delete five most recent dates
    for event_date in event.event_dates[5:]:
        db.session.delete(event_date)
    db.session.commit()
    assert len(event.event_dates) == 5
    event_dates.generate_future_event_dates(event, rrule=rrule)
    future_event_dates = event.future_event_dates
    for index, ed in enumerate(future_event_dates):
        if index == 0:
            pass
        else:

            print("start", ed.start)
            print("weekday", ed.start.weekday())
            # there should be a year between each event_date
            next_expected_date = future_event_dates[index - 1].start + relativedelta(
                years=1
            )
            assert ed.start.year == next_expected_date.year
            # it should be on the same week of the month
            # eg. first saturday of january
            # as in first_saturday_of_next_month_at_1330pm fixture
            assert ed.start.weekday() == 5
            # assert ed.start.month == // too annoying to test
    assert len(event.future_event_dates) == 10


def test_generate_future_event_dates_for_event_partial_yearly_absolute(
    regular_user, complete_event_factory, rrule_factory, db
):
    event = complete_event_factory()
    start_date = event.event_dates[0].start
    # event should have one event date by default
    assert len(event.future_event_dates) == 1
    rrule = {  # every month on the 1st day
        "recurring_type": 3,
        "separation_count": 1,
        "day_of_week": 4,
        "week_of_month": None,
        "day_of_month": 1,
        # "month_of_year": 5, unused
    }
    rrule = rrule_factory(event, rrule)
    event_dates.generate_future_event_dates(event, rrule=rrule)
    # delete five most recent dates
    for event_date in event.event_dates[5:]:
        db.session.delete(event_date)
    db.session.commit()
    assert len(event.event_dates) == 5
    event_dates.generate_future_event_dates(event, rrule=rrule)
    future_event_dates = event.future_event_dates
    for index, ed in enumerate(future_event_dates):
        if index == 0:
            pass
        else:
            # there should be a month between each event_date
            next_expected_date = future_event_dates[index - 1].start + relativedelta(
                years=1
            )
            assert ed.start.year == next_expected_date.year
            assert ed.start.day == start_date.day
            assert ed.start.month == start_date.month
    assert len(event.future_event_dates) == 10


def test_generate_future_event_dates_for_event_partial_monthly_absolute(
    regular_user, complete_event_factory, rrule_factory, db
):
    event = complete_event_factory()
    start_date = event.event_dates[0].start
    # event should have one event date by default
    assert len(event.future_event_dates) == 1
    rrule = {  # every month on the 1st day
        "recurring_type": 2,
        "separation_count": 1,
        "day_of_week": 4,
        "week_of_month": None,
        "day_of_month": 1,
        # "month_of_year": 5, unused
    }
    rrule = rrule_factory(event, rrule)
    event_dates.generate_future_event_dates(event, rrule=rrule)
    # delete five most recent dates
    for event_date in event.event_dates[5:]:
        db.session.delete(event_date)
    db.session.commit()
    assert len(event.event_dates) == 5
    event_dates.generate_future_event_dates(event, rrule=rrule)
    future_event_dates = event.future_event_dates
    for index, ed in enumerate(future_event_dates):
        if index == 0:
            pass
        else:
            # there should be a month between each event_date
            next_expected_date = future_event_dates[index - 1].start + relativedelta(
                months=1
            )
            assert ed.start.month == next_expected_date.month
            assert (
                ed.start.day == start_date.day
            )  # should be same day as original start date

    assert len(event.future_event_dates) == 10


def test_query_event_dates_bounds(
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
        "_southWest": {"lat": -61.85614879566797, "lng": 130.34179687500003},
        "_northEast": {"lat": 2.0210651187669897, "lng": 247.23632812500003},
    }

    dates = event_dates.query_event_dates(bounds=bounds)
    assert len(dates.items) == 1

    bounds = {  # roughly the area around barcenlona
        "_northEast": {"lat": -20.961440, "lng": 209.443359},
        "_southWest": {"lat": -53.357109, "lng": 135.395508},
    }
    dates = event_dates.query_event_dates(bounds=bounds)
    assert len(dates.items) == 1

    bounds = {  # roughly the area around new york
        "_northEast": {"lat": 46.255847, "lng": -413.569336},
        "_southWest": {"lat": 30.429730, "lng": -450.483398},
    }
    dates = event_dates.query_event_dates(bounds=bounds)
    assert len(dates.items) == 0


def test_query_event_dates_bounds_tags(
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
    dates = event_dates.query_event_dates(bounds=bounds)
    assert len(dates.items) == 1

    # rougly the area of nz negative longitude
    bounds = {
        "_northEast": {"lat": 48.922499263758255, "lng": -62.57812500000001},
        "_southWest": {"lat": -72.23551372557404, "lng": -254.53125000000003},
    }
    dates = event_dates.query_event_dates(bounds=bounds)
    assert len(dates.items) == 1

    bounds = {  # roughly the whole world
        "_northEast": {"lat": 90, "lng": 180},
        "_southWest": {"lat": -90, "lng": -180},
    }
    dates = event_dates.query_event_dates(bounds=bounds)
    assert len(dates.items) == 2

    dates = event_dates.query_event_dates(bounds=bounds, tags=["barca"])
    assert len(dates.items) == 1

    bounds = {  # roughly barcelona
        "_southWest": {"lat": 35.191766965947394, "lng": -10.832519531250002},
        "_northEast": {"lat": 50.035973672195496, "lng": 13.16162109375},
    }
    dates = event_dates.query_event_dates(bounds=bounds, tags=["barca"])
    assert len(dates.items) == 1

    bounds = {  # roughly barcelona
        "_southWest": {"lat": 17.14079039331665, "lng": -177.89062500000003},
        "_northEast": {"lat": 85.0511287798066, "lng": 14.062500000000002},
    }
    dates = event_dates.query_event_dates(bounds=bounds, tags=["barca"])
    assert len(dates.items) == 1

    bounds = {
        "_southWest": {"lat": -71.41317683396566, "lng": -16.523437500000004},
        "_northEast": {"lat": 50.62507306341437, "lng": 175.42968750000003},
    }
    dates = event_dates.query_event_dates(bounds=bounds, tags=["barca"])
    assert len(dates.items) == 1

    bounds = {  # roughly barcelona
        "_southWest": {"lat": 35.191766965947394, "lng": -10.832519531250002},
        "_northEast": {"lat": 50.035973672195496, "lng": 13.16162109375},
    }
    dates = event_dates.query_event_dates(bounds=bounds, tags=["timaru"])
    assert len(dates.items) == 0


def test_query_event_dates_bounds_tags_dates(
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
    dates = event_dates.query_event_dates(
        bounds=bounds,
        date_min=first_saturday_of_next_month_at_1330pm(),
        date_max=first_saturday_of_next_month_at_1330pm() + relativedelta(days=1),
    )
    assert len(dates.items) == 1

    dates = event_dates.query_event_dates(
        bounds=bounds,
        date_min=first_saturday_of_next_month_at_1330pm(),
    )
    assert len(dates.items) == 1

    bounds = {  # roughly the whole world
        "_northEast": {"lat": 90, "lng": 180},
        "_southWest": {"lat": -90, "lng": -180},
    }
    dates = event_dates.query_event_dates(bounds=bounds, date_min=day_after_tomorrow)
    assert len(dates.items) == 1  # only timaru party

    dates = event_dates.query_event_dates(
        bounds=bounds, date_min=tomorrow, date_max=day_after_tomorrow
    )
    assert len(dates.items) == 1  # only barcelona party


def test_query_event_dates_relative_location(
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

    # rougly nz
    location = {"lat": -61.85614879566797, "lng": 130.34179687500003}
    dates = event_dates.query_event_dates(location=location)
    assert dates.items[0].distance == 3288279.89762588  # distance in meters

    # exact location of barcelona event
    location = {"lat": 41.426253, "lng": 1.933594}
    dates = event_dates.query_event_dates(location=location)
    for event in dates.items:
        print(event.distance, event.location.name)
    assert dates.items[0].distance == 0  # distance in meters

    # exact location of timaru event
    location = {"lat": -44.386692, "lng": 171.562500}
    dates = event_dates.query_event_dates(location=location)
    assert dates.items[0].distance == 0  # distance in meters


def test_query_event_dates_relative_location_tags(
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

    # rougly nz
    location = {"lat": -61.85614879566797, "lng": 130.34179687500003}
    dates = event_dates.query_event_dates(location=location, tags=["timaru"])
    assert dates.items[0].distance == 3288279.89762588  # distance in meters

    # exact location of barcelona event
    location = {"lat": 41.426253, "lng": 1.933594}
    dates = event_dates.query_event_dates(location=location, tags=["barca"])
    for event in dates.items:
        print(event.distance, event.location.name)
    assert dates.items[0].distance == 0  # distance in meters

    # exact location of barcelona event
    location = {"lat": 41.426253, "lng": 1.933594}
    dates = event_dates.query_event_dates(location=location, tags=["barcawer"])
    for event in dates.items:
        print(event.distance, event.location.name)
    assert len(dates.items) == 0  # distance in meters


def test_query_event_date(complete_event_factory):
    event = complete_event_factory()
    # there should be one event date
    assert len(event.event_dates) == 1
    ed = event_dates.get_event_date_or_404(event.event_dates[0].id)
    assert ed.id == event.event_dates[0].id
