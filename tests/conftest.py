from pmapi.application import create_app
from pmapi.extensions import db as _db
from pmapi.user.model import User
from pmapi.event.model import Event
from pmapi.config import BaseConfig
from pmapi.extensions import mail

from flask_login import AnonymousUserMixin
import pytest


class Config_Test(BaseConfig):
    ENV = "testing"
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "postgresql:///partymap-testing"
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
def db(app):
    """A database for the tests."""
    _db.app = app
    with app.app_context():
        _db.create_all()

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
        db = request.getfixturevalue("db")
        meta = db.metadata
        for table in meta.sorted_tables:
            db.session.execute(table.delete())
        db.session.commit()

    if "db" in request.fixturenames:
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
        # user.client = app.test_client(username=username, password=password)

        return user

    return _gen_user


@pytest.fixture
def event_factory(app, db, regular_user):
    """Factory function for creating events in the db."""

    def _gen_event(name):
        event = Event(
            name=name,
            creator_id=regular_user.id,
            default_url="test.com",
            description="test event",
        )

        db.session.add(event)
        db.session.commit()

        # Patch a web client for making authenticated requests onto the user
        # user.client = app.test_client(username=username, password=password)

        return event

    return _gen_event


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
