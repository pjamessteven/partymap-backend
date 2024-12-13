"""
application.py
- creates a Flask app instance and registers the database object
"""

from flask import Flask, session, render_template, request, g, jsonify
from flask_cors import cross_origin
from flask.helpers import get_debug_flag
import psycopg2
# from flask_dance.consumer.storage.sqla import SQLAlchemyStorage
# from flask_dance.contrib.facebook import make_facebook_blueprint, facebook
# from sqlalchemy_continuum import make_versioned
from flask_login import current_user, AnonymousUserMixin
from datetime import datetime
from flask_migrate import Migrate

from pmapi import extensions
from pmapi.user.model import User

from .exceptions import DatabaseConnectionError
from .exceptions import InvalidAPIRequest
from .exceptions import InvalidRoute
from .exceptions import JSONException
from .exceptions import RecordAlreadyExists
from .exceptions import SystemError

from .extensions import db

from sqlalchemy.exc import DatabaseError
from sqlalchemy.exc import DBAPIError
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import InternalServerError
from werkzeug.exceptions import UnprocessableEntity
from werkzeug.routing import RequestRedirect

from flask_track_usage.storage.sql import SQLStorage
from .config import DevConfig, ProdConfig

import os
import logging
from pmapi.utils import ROLES, SUPPORTED_LANGUAGES
from pmapi.scripts import update_translations
# ONLY FOR TESTING !!
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

DEV_ENVIRON = get_debug_flag()

CONFIG = DevConfig if DEV_ENVIRON else ProdConfig


class AnonUser(AnonymousUserMixin):
    id = CONFIG.ANON_USER_ID
    role = ROLES["UNPRIVILIGED_USER"]

    def get_id(self):
        return CONFIG.ANON_USER_ID


def create_app(config=CONFIG, app_name="PARTYMAP"):
    app = Flask(app_name)
    migrate = Migrate(app, db)

    app.config.from_object(config)
    register_blueprints(app)
    register_extensions(app)
    register_blueprints_with_tracker(app)
    extensions.lm.login_view = "auth.LoginResource"
    register_errorhandlers(app)
    register_docs(app)

    @app.route('/oauth_redirect')
    def index():
        redirect_uri = request.args.get('redirect_uri')
        return render_template('oauth_redirect.html', redirect_uri=redirect_uri)

    @app.before_request
    def update_last_active():
        if current_user and current_user.is_authenticated:
            current_user.last_active = datetime.utcnow()
            extensions.db.session.add(current_user)
            extensions.db.session.commit()


    @app.after_request
    def add_partitioned_cookie(response):
        cookie_header = response.headers.get('Set-Cookie')
        if cookie_header:
            if isinstance(cookie_header, str):
                response.headers['Set-Cookie'] = cookie_header + '; Partitioned'
            elif isinstance(cookie_header, list):
                response.headers['Set-Cookie'] = [h + '; Partitioned' for h in cookie_header]
        return response

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        if exception:
            db.session.rollback()  # Rollback any uncommitted transaction
        db.session.remove()
        
    with app.app_context():
        from pmapi import event_listeners  # Import here to avoid circular imports
        # create and set anonymous user
        """
        anon = (
            extensions.db.session.query(User)
            .filter(User.username == "anon")
            .first()
        )
        if anon is None:
            # create anon user if not already created
            anon = User(
                username="anon",
                email="anon@partymap.com",
                status="active",
                id=config.ANON_USER_ID,
            )
            extensions.db.session.add(anon)
            extensions.db.session.commit()

        system = (
            extensions.db.session.query(User)
            .filter(User.username == "partymap-bot")
            .first()
        )
        if system is None:
            # create anon user if not already created
            system = User(
                username="partymap-bot",
                email="info@partymap.com",
                status="active",
                id=config.SYSTEM_USER_ID,
            )
            extensions.db.session.add(system)
            extensions.db.session.commit()
        """
        extensions.lm.anonymous_user = AnonUser

    if config.DEBUG is True:
        # used for serving files with dev server
        @app.route("/<path:path>")
        @cross_origin()
        def static_file(path):
            return app.send_static_file(path)

    @app.cli.command("update-translation")
    def update_translation():
        return update_translations()


    return app


def register_extensions(app):
    extensions.cache.init_app(app)
    try:
        extensions.db.init_app(app)
    except:
        print("Error initiating db extension")
        pass
    extensions.admin.init_app(app)
    extensions.lm.init_app(app)
    extensions.cors.init_app(app)
    extensions.mail.init_app(app)
    extensions.apidocs.init_app(app)
    # extensions.babel.init_app(app)
   #  extensions.babel.localeselector(get_locale)

    with app.app_context():
        try:
            extensions.tracker.init_app(
                app,
                [
                    SQLStorage(db=db),
                ],
            )
        except:
            print("Error initiating tracker, likely due to db problem.")
            pass


def register_blueprints(app):
    from pmapi.auth.oauth_fb_resource import oauth_fb_blueprint
    from pmapi.auth.oauth_google_resource import oauth_google_blueprint
    from pmapi.auth.resource import auth_blueprint
    from pmapi.event_tag.resource import event_tags_blueprint
    from pmapi.event_date.resource import event_dates_blueprint
    from pmapi.event.resource import events_blueprint
    from pmapi.event_location.resource import locations_blueprint
    from pmapi.media_item.resource import media_blueprint
    from pmapi.user.resource import users_blueprint
    from pmapi.report.resource import reports_blueprint
    from pmapi.feedback.resource import feedback_blueprint
    from pmapi.suggestions.resource import suggestions_blueprint
    from pmapi.event_artist.resource import artists_blueprint
    from pmapi.services.resource import services_blueprint

    from pmapi.event_review.resource import event_review_blueprint
    from pmapi.search.resource import search_blueprint

    # from pmapi.favorite_events.resource import favorites_blueprint
    from pmapi.activity.resource import activity_blueprint

    # auth endpoint is /api/oauth/google
    app.register_blueprint(oauth_google_blueprint, url_prefix="/api/oauth")
    # auth endpoint is /api/oauth/facebook
    app.register_blueprint(oauth_fb_blueprint, url_prefix="/api/oauth")
    app.register_blueprint(auth_blueprint, url_prefix="/api/auth")
    app.register_blueprint(event_tags_blueprint, url_prefix="/api/tag")
    app.register_blueprint(event_dates_blueprint, url_prefix="/api/date")
    app.register_blueprint(events_blueprint, url_prefix="/api/event")
    app.register_blueprint(media_blueprint, url_prefix="/api/media")
    app.register_blueprint(locations_blueprint, url_prefix="/api/location")
    app.register_blueprint(users_blueprint, url_prefix="/api/user")
    app.register_blueprint(event_review_blueprint,
                           url_prefix="/api/contribution")
    # app.register_blueprint(favorites_blueprint, url_prefix="/api/favorites")
    app.register_blueprint(activity_blueprint, url_prefix="/api/activity")
    app.register_blueprint(reports_blueprint, url_prefix="/api/report")
    app.register_blueprint(feedback_blueprint, url_prefix="/api/feedback")
    app.register_blueprint(suggestions_blueprint,
                           url_prefix="/api/suggestions")
    app.register_blueprint(artists_blueprint, url_prefix="/api/artist")
    app.register_blueprint(search_blueprint, url_prefix="/api/search")
    app.register_blueprint(services_blueprint, url_prefix="/api/services")


def register_blueprints_with_tracker(app):
    from pmapi.extensions import tracker

    # from pmapi.auth.oauth_resource import oauth_blueprint this one causes issues
    from pmapi.auth.resource import auth_blueprint
    from pmapi.event_tag.resource import event_tags_blueprint
    from pmapi.event_date.resource import event_dates_blueprint
    from pmapi.event.resource import events_blueprint
    from pmapi.event_location.resource import locations_blueprint
    from pmapi.media_item.resource import media_blueprint
    from pmapi.user.resource import users_blueprint
    from pmapi.report.resource import reports_blueprint
    from pmapi.feedback.resource import feedback_blueprint
    from pmapi.suggestions.resource import suggestions_blueprint
    from pmapi.event_artist.resource import artists_blueprint
    from pmapi.search.resource import search_blueprint

    tracker.include_blueprint(auth_blueprint)
    tracker.include_blueprint(event_tags_blueprint)
    tracker.include_blueprint(event_dates_blueprint)
    tracker.include_blueprint(events_blueprint)
    tracker.include_blueprint(locations_blueprint)
    tracker.include_blueprint(media_blueprint)
    tracker.include_blueprint(users_blueprint)
    tracker.include_blueprint(reports_blueprint)
    tracker.include_blueprint(feedback_blueprint)
    tracker.include_blueprint(suggestions_blueprint)
    tracker.include_blueprint(artists_blueprint)
    tracker.include_blueprint(search_blueprint)


def register_docs(app):
    from pmapi.auth.resource import (
        LoginResource,
        LogoutResource,
    )
    from pmapi.user.resource import UsersResource
    from pmapi.event_tag.resource import TagsResource
    from pmapi.event_location.resource import (
        PointsResource,
        LocationResource,
        LocationsResource,
    )
    from pmapi.event_date.resource import (
        DateResource,
        DatesResource,
        EventDatesResource,
    )
    from pmapi.event.resource import (
        EventResource,
        EventsResource,
    )
    from pmapi.suggestions.resource import (
        SuggestedEditResource,
        SuggestedEditsResource,
    )
    from pmapi.event_artist.resource import (
        ArtistResource,
    )
    from pmapi.services.resource import IpLookupResource

    extensions.apidocs.register(LoginResource, "auth.LoginResource")
    extensions.apidocs.register(LogoutResource, "auth.LogoutResource")
    extensions.apidocs.register(UsersResource, "users.UsersResource")
    extensions.apidocs.register(TagsResource, "tags.TagsResource")
    extensions.apidocs.register(PointsResource, "locations.PointsResource")
    extensions.apidocs.register(LocationResource, "locations.LocationResource")
    extensions.apidocs.register(
        LocationsResource, "locations.LocationsResource")
    extensions.apidocs.register(DateResource, "dates.DateResource")
    extensions.apidocs.register(DatesResource, "dates.DatesResource")
    extensions.apidocs.register(EventDatesResource, "dates.EventDatesResource")
    extensions.apidocs.register(EventResource, "events.EventResource")
    extensions.apidocs.register(EventsResource, "events.EventsResource")
    extensions.apidocs.register(
        SuggestedEditsResource, "suggestions.SuggestedEditsResource"
    )
    extensions.apidocs.register(
        SuggestedEditResource, "suggestions.SuggestedEditResource"
    )
    extensions.apidocs.register(ArtistResource, "artists.ArtistResource")
    extensions.apidocs.register(IpLookupResource, "service.IpLookupResource")


def register_errorhandlers(app):
    app.errorhandler(JSONException)(handle_error)
    app.errorhandler(UnprocessableEntity.code)(handle_webargs_error)
    app.errorhandler(RequestRedirect)(handle_301)
    app.register_error_handler(InternalServerError, handle_internal_error)
    app.errorhandler(DBAPIError)(handle_db_disconnect)
    app.errorhandler(DatabaseError)(handle_db_disconnect)
    app.errorhandler(IntegrityError)(handle_integrity_error)


def handle_internal_error(error, **kwargs):
    error = SystemError()
    return handle_error(error)


def handle_301(error):
    response = jsonify(InvalidRoute(
        message={"new_url": error.new_url}).to_dict())
    return response


def handle_error(error, origin_error=None):
    error_dict = error.to_dict()
    response = jsonify(error_dict)
    response.status_code = error.status_code
    logging.error("{} error".format(error.__class__.__name__))
    logging.error(f"Root cause: {origin_error}")
    return response


# # webargs raises 422 UnprocessableEntity on parse errors
def handle_webargs_error(error):
    data = getattr(error, "data", None)
    if data:
        # Get validations from the ValidationError object
        messages = data.get("messages")
    else:
        messages = [getattr(error, "description", "Invalid Request")]
    error = InvalidAPIRequest(message=messages, status_code=400)
    return handle_error(error)


def handle_db_disconnect(error):
    if error.connection_invalidated:
        try:
            db.session.rollback()
        except Exception:
            pass
    error = DatabaseConnectionError()
    return handle_error(error)


def handle_integrity_error(original_error):
    error = RecordAlreadyExists()
    return handle_error(error, original_error)

