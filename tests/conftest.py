from pmapi.application import create_app
from pmapi.extensions import db as _db
from pmapi.user.model import User
from pmapi.event.model import Event, Rrule
from pmapi.event_location.model import EventLocation, EventLocationType, Country, Region, Locality
from pmapi.event_tag.model import Tag, EventTag
from pmapi.config import BaseConfig
from pmapi.extensions import mail
import pmapi.exceptions as exc
import pygeohash as pgh
from datetime import datetime
from dateutil.relativedelta import relativedelta
from flask_login import AnonymousUserMixin
from flask import url_for
from flask_migrate import upgrade
import pytest
import uuid
from sqlalchemy import func, and_, Index, ForeignKeyConstraint
from unittest.mock import patch

import pmapi.event_date.controllers as event_dates


class Config_Test(BaseConfig):
    ENV = "testing"
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "postgresql://partymap:password@test-db:5432/partymap"
    # PRESERVE_CONTEXT_ON_EXCEPTION = False


@pytest.fixture(scope="session")
def config():
    return Config_Test()


@pytest.fixture(scope="session")
def app(config):
    """An application for the tests."""
    _app = create_app(config)

    ctx = _app.app_context()
    ctx.push()

    yield _app

    ctx.pop()

        
@pytest.fixture(scope="session")
def db(app, config):
    """A database for the tests."""
    _db.app = app
    with app.app_context():
        print('SETUP DB')
        _db.engine.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
        _db.engine.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        _db.engine.execute("CREATE EXTENSION IF NOT EXISTS hstore;")
        _db.create_all()
        # configure anon user
        anon = (
            _db.session.query(User)
            .filter(User.username == "anon")
            .first()
        )
        if anon is None:
            print('CREATING ANON')
            anon = User(
                username="anon",
                email="anon@partymap.com",
                status="active",
                id=config.ANON_USER_ID,
            )
            _db.session.add(anon)
            _db.session.commit()

        # upgrade()

    yield _db

    # Explicitly close DB connection
    _db.session.close()
    _db.drop_all()


@pytest.fixture(autouse=True)
def clear_db(request):
    """
    This fixture will be used by every test and checks if the test uses db.
    If it does, it deletes the content of the database, so the test has a
    fresh db to work with.
    """

    def _clear_db():
        print('CLEARING DB')

        db = request.getfixturevalue("db")
        meta = db.metadata
        print('CLEARED DB2')

        # Rollback any pending transaction from a failed test
        try:
            db.session.rollback()
        except Exception:
            pass

        # Delete all rows using truncate cascade to handle fk ordering
        with db.engine.begin() as conn:
            for table in reversed(meta.sorted_tables):
                print('table', table)
                conn.execute(f"TRUNCATE TABLE {table.name} CASCADE")
        print('CLEARED DB3')

        # Drop the indexes
        try:
            with db.engine.begin() as conn:
                event_index = Index("idx_events_fts", "events.c.__ts_vector__")
                event_index.drop(conn)
                tag_index = Index("idx_tags_fts", "tags.c.__ts_vector__")
                tag_index.drop(conn)
        except Exception:
            pass
        print('CLEARED DB4')
        print('CLEARED DB3')

        # Drop the indexes
        try:
            with db.engine.connect() as conn:
                event_index = Index("idx_events_fts", "events.c.__ts_vector__")
                event_index.drop(conn)
                tag_index = Index("idx_tags_fts", "tags.c.__ts_vector__")
                tag_index.drop(conn)
        except Exception:
            pass
        print('CLEARED DB4')

        db.session.commit()

    if "db" in request.fixturenames:
        print('CLEAR DB')
        request.addfinalizer(_clear_db)


@pytest.fixture
def user_factory(app, db):
    """Factory function for creating users in the db.
    Also adds a 'client' property to the user which is a webclient that is
    authenticated as that user."""

    def _gen_user(
        username,
        role=10,
        status="active",
        password="password",
    ):
        username = username.lower()
        user = User(
            username=username,
            password=password,
            email="{}@example.com".format(username),
            role=role,
            status=status,
        )

        db.session.add(user)
        db.session.commit()

        # Patch a web client for making authenticated requests onto the user
        user.client = app.test_client()
        print(user.email)

        # log in to client
        payload = {"email": "{}@example.com".format(username), "password": password}
        user.client.post(
            url_for("auth.LoginResource"), json=payload, follow_redirects=True
        )
        return user

    return _gen_user


@pytest.fixture
def first_saturday_of_next_month_at_1330pm():
    def _gen_date():
        a_month_from_now = datetime.now() + relativedelta(months=1)
        first_day_of_next_month = a_month_from_now.replace(day=1)
        first_day_of_next_month = first_day_of_next_month.replace(
            hour=13, minute=30, second=0, microsecond=0, tzinfo=None
        )
        first_saturday_of_next_month = None

        for x in range(0, 7):
            date = first_day_of_next_month + relativedelta(days=x)
            # find first saturday
            if date.weekday() == 5:
                first_saturday_of_next_month = date
                break

        return first_saturday_of_next_month

    return _gen_date


@pytest.fixture
def complete_event_factory(
    app,
    db,
    regular_user,
    event_factory,
    event_date_factory,
    event_tag_factory,
    event_location_factory,
    first_saturday_of_next_month_at_1330pm,
):
    """
    Factory function for creating complete events in the db.
    Includes event tags, event date and event location.
    """
    start = first_saturday_of_next_month_at_1330pm()

    def _gen_event(
        name="test event",
        description="description",
        tags=["test1", "test2"],
        start=start,
        end=None,
        creator=regular_user,
        event_location=None,
    ):
        if not event_location:
            event_location = event_location_factory(
                geometry={"location": {"lat": -44.3903881, "lng": 171.2372756}}
            )
        event = event_factory(
            name=name, location=event_location, description=description, creator=creator
        )
        event_tag_factory(tags=tags, event=event)
        event_date_factory(start, end, event, event_location)

        return event

    return _gen_event


@pytest.fixture
def event_factory(app, db, regular_user, user_factory):
    """Factory function for creating events in the db."""

    def _gen_event(
        name="test event",
        location=None,
        description="description",
        creator=regular_user,
    ):
        event = Event(
            name=name,
            creator_id=creator.id,
            description=description,
        )

        db.session.add(event)
        db.session.commit()

        # Patch a web client for making authenticated requests onto the user
        # user.client = app.test_client(username=username, password=password)

        return event

    return _gen_event


@pytest.fixture
def event_date_factory(
    app,
    db,
    regular_user,
    event_factory,
    event_location_factory,
    first_saturday_of_next_month_at_1330pm,
):
    """Factory function for creating events in the db."""
    start = first_saturday_of_next_month_at_1330pm()

    def _gen_event_date(
        start_naive=start,
        end_naive=None,
        event=None,
        event_location=None,
        creator=regular_user,
    ):

        if event is None:
            event = event_factory(creator=creator)
        if event_location is None:
            event_location = event_location_factory()
        ed = event_dates.add_event_date(
            start_naive,
            end_naive,
            event,
            event_location=event_location,
            url="https://test.com",
            creator=creator,
        )

        # Patch a web client for making authenticated requests onto the user
        # user.client = app.test_client(username=username, password=password)

        return ed

    return _gen_event_date


@pytest.fixture
def rrule_factory(app, db, regular_user):
    """Factory function for creating events in the db."""

    def _gen_rrule(
        event,
        rrule={  # every month on the 1st day
            "recurring_type": 2,
            "separation_count": 1,
            "day_of_week": 4,
            "week_of_month": None,
            "day_of_month": 1,
            "month_of_year": 5,
        },
    ):
        rrule = Rrule(event=event, **rrule)
        db.session.add(rrule)
        db.session.commit()

        # Patch a web client for making authenticated requests onto the user
        # user.client = app.test_client(username=username, password=password)

        return rrule

    return _gen_rrule


@pytest.fixture
def event_tag_factory(app, db, regular_user, event_factory):
    """Factory function for creating events in the db."""

    def _gen_event_tags(tags=["test"], event=None):
        if event is None:
            event = event_factory()
        event_tags = []
        for t in tags:
            tag = Tag(tag=t)

            # check if tag is already in db
            if db.session.query(Tag).filter(Tag.tag == t).count():
                tag = db.session.query(Tag).filter(Tag.tag == t).one()

            # don't add duplicate event tag
            if (
                db.session.query(EventTag)
                .filter(EventTag.tag == tag, EventTag.event == event)
                .count()
            ):
                raise exc.RecordAlreadyExists("Tag already exists for event")

            et = EventTag(tag=tag, event=event, creator_id=regular_user.id)
            db.session.add(et)
            event_tags.append(et)

        db.session.commit()

        return event_tags

    return _gen_event_tags


@pytest.fixture
def event_location_type_factory(app, db, regular_user):
    """Factory function for creating events location types in the db."""

    def _gen_event_location_type(type="test type"):
        el_type = None
        # check if type is already in db
        if (
            db.session.query(EventLocationType)
            .filter(EventLocationType.type == type)
            .count()
        ):
            el_type = (
                db.session.query(EventLocationType)
                .filter(EventLocationType.type == type)
                .one()
            )
        else:
            el_type = EventLocationType(type=type)
            db.session.add(el_type)
            db.session.commit()

        # Patch a web client for making authenticated requests onto the user
        # user.client = app.test_client(username=username, password=password)

        return el_type

    return _gen_event_location_type


@pytest.fixture
def event_location_factory(app, db, regular_user, event_location_type_factory):
    """Factory function for creating events in the db."""

    def _gen_event_location(
        name="place name",
        geometry={"location": {"lat": -44.3903881, "lng": 171.2372756}},
        address_components=None,
    ):
        place_id = str(uuid.uuid4())  # random primary key
        description = name
        types = [
            event_location_type_factory(type="locality"),
            event_location_type_factory(type="political"),
        ]

        lat = float(geometry["location"]["lat"])
        lng = float(geometry["location"]["lng"])

        # Default address components if none provided
        if address_components is None:
            address_components = [
                {"long_name": "Timaru", "short_name": "Timaru", "types": ["locality", "political"]},
                {"long_name": "Canterbury", "short_name": "Canterbury", "types": ["administrative_area_level_1", "political"]},
                {"long_name": "New Zealand", "short_name": "NZ", "types": ["country", "political"]},
            ]

        # Create country, region, locality from address_components
        country = None
        region = None
        locality = None
        for component in address_components:
            if "country" in component["types"]:
                country = db.session.query(Country).filter_by(short_name=component["short_name"]).first()
                if not country:
                    country = Country(short_name=component["short_name"], long_name=component["long_name"])
                    db.session.add(country)
                    db.session.flush()
            elif "administrative_area_level_1" in component["types"]:
                region = db.session.query(Region).filter_by(short_name=component["short_name"], country=country).first()
                if not region:
                    region = Region(short_name=component["short_name"], long_name=component["long_name"], country=country)
                    db.session.add(region)
                    db.session.flush()
            elif "locality" in component["types"]:
                locality = db.session.query(Locality).filter_by(short_name=component["short_name"], region=region, country=country).first()
                if not locality:
                    locality = Locality(short_name=component["short_name"], long_name=component["long_name"], region=region, country=country)
                    db.session.add(locality)
                    db.session.flush()

        el = EventLocation(
            geohash=pgh.encode(lat, lng),
            # For geodetic coordinates,
            # X is longitude and Y is latitude
            geo="SRID=4326;POINT ({0} {1})".format(lng, lat),
            name=name,
            description=description,
            types=types,
            lat=lat,
            lng=lng,
            place_id=place_id,
            creator_id=regular_user.id,
            country=country,
            region=region,
            locality=locality,
        )
        db.session.add(el)
        db.session.commit()

        return el

    return _gen_event_location


@pytest.fixture
def admin_user(db, user_factory):
    """Admin user for the tests."""
    admin = user_factory(username="admin", role=30, password="admin_password")
    return admin


@pytest.fixture
def staff_user(db, user_factory):
    """Staff user for the tests."""
    staff = user_factory(username="staff", role=20, password="staff_password")
    return staff


@pytest.fixture
def regular_user(db, user_factory):
    """Regular user for the tests."""
    return user_factory(
        username="regular_user",
        role=10,
        password="user_password",
    )


@pytest.fixture
def regular_user_factory(db, user_factory):
    """Regular user factory for the tests."""

    def _gen_regular_user():
        return user_factory(
            username=str(uuid.uuid4()),
            role=10,
            password="password",
        )

    return _gen_regular_user


@pytest.fixture
def anon_user(app):
    """
    Anon user with patched client so we can make unauthenticated requests
    """
    anon_user = AnonymousUserMixin()
    anon_user.client = app.test_client()

    return anon_user


@pytest.fixture
def emailer():
    """Fixture to be used whenever testing the extension we use to send system email.
    When app.testing is True, then the mailer doesn't send anything but instead records
    the mail that would've been sent. Because this extension is tied to the "app", and
    the app lives for the duration of the test session, this mail_sent count accumulates
    across test boundaries and so must be reset between tests to give an accurate count
    of mail sent for each test.
    """
    mail.reset_mail_sent()
    return mail


# ---------------------------------------------------------------------------
# Mock fixtures for external services (Google Maps, image downloads, etc.)
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_gmaps_resolve():
    """Patch Google Maps geocoding so tests can send a simple location string."""
    fake_place = {
        "place_id": "ChIJ78dhY4ljLG0ROZl5hIbvAAU",
        "name": "Timaru",
        "description": "Timaru, New Zealand",
        "types": ["locality", "political"],
        "geometry": {
            "location": {"lat": -44.3903881, "lng": 171.2372756},
            "viewport": {
                "south": -44.42603005279609,
                "west": 171.1740580162034,
                "north": -44.33174896335244,
                "east": 171.272916966389,
            },
        },
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
    }
    with patch(
        "pmapi.services.gmaps.get_best_location_result",
        return_value=fake_place,
    ) as mock:
        yield mock


@pytest.fixture
def mock_image_download():
    """Patch image URL downloading so tests can use fake remote image URLs."""
    fake_base64 = "data:image/webp;base64,UklGRiIAAABXRUJQVlA4IBYAAAAwAQCdASoBAAEADsD+JaQAA3AAAAAA"
    with patch(
        "pmapi.media_item.controllers.download_image_as_base64",
        return_value=fake_base64,
    ) as mock:
        yield mock


@pytest.fixture
def mock_hcaptcha():
    """Patch hCaptcha validation so anon suggestion tests don't need real tokens."""
    with patch(
        "pmapi.hcaptcha.controllers.validate_hcaptcha",
        return_value=True,
    ) as mock:
        yield mock


@pytest.fixture
def mock_apple_auth():
    """Patch Apple Sign-In authentication to return a fake user."""
    fake_user = {"sub": "apple-id-123", "email": "apple@example.com"}
    with patch(
        "pmapi.auth.controllers.authenticate_apple_user",
        return_value=fake_user,
    ) as mock:
        yield mock


@pytest.fixture(autouse=True)
def mock_generate_embedding():
    """Patch embedding generation to return None in tests (avoids external API calls).
    Must patch where it's used (pmapi.event.controllers), not where it's defined."""
    with patch(
        "pmapi.event.controllers.generate_embedding",
        return_value=None,
    ) as mock:
        yield mock
