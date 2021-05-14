"""
application.py
- creates a Flask app instance and registers the database object
"""

from flask import Flask
from flask_cors import cross_origin

# from flask_dance.consumer.storage.sqla import SQLAlchemyStorage
# from flask_dance.contrib.facebook import make_facebook_blueprint, facebook
# from sqlalchemy_continuum import make_versioned
from flask_login import current_user
from datetime import datetime
from flask import jsonify

from pmapi import extensions
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

import os
import logging

# ONLY FOR TESTING !!
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"


def create_app(config, app_name="PARTYMAP"):
    app = Flask(app_name)
    app.config.from_object(config)

    register_extensions(app)
    register_blueprints(app)
    register_errorhandlers(app)
    register_docs(app)

    @app.before_request
    def update_last_active():
        print("is authenticated?")
        print(current_user)
        print(current_user.is_anonymous)
        print(current_user.is_authenticated)
        if current_user.is_authenticated:
            current_user.last_active = datetime.utcnow()
            extensions.db.session.add(current_user)
            extensions.db.session.commit()

    # potential security risk?
    @app.route("/<path:path>")
    @cross_origin()
    def static_file(path):
        print("test")
        return app.send_static_file(path)

    return app


def register_extensions(app):
    extensions.cache.init_app(app)
    extensions.db.init_app(app)
    extensions.admin.init_app(app)
    extensions.lm.init_app(app)
    extensions.cors.init_app(app)
    extensions.lm.login_view = "auth.LoginResource"
    extensions.mail.init_app(app)
    extensions.apidocs.init_app(app)


def register_blueprints(app):
    # from pmapi.auth.oauth_resource import oauth_blueprint
    from pmapi.auth.resource import auth_blueprint
    from pmapi.event_tag.resource import event_tags_blueprint
    from pmapi.event_date.resource import event_dates_blueprint
    from pmapi.event.resource import events_blueprint
    from pmapi.event_location.resource import locations_blueprint
    from pmapi.user.resource import users_blueprint

    # from pmapi.event_contribution.resource import event_contribution_blueprint
    # from pmapi.favorite_events.resource import favorites_blueprint
    from pmapi.activity.resource import activity_blueprint

    # app.register_blueprint(oauth_blueprint, url_prefix="/api/oauth")
    app.register_blueprint(auth_blueprint, url_prefix="/api/auth")
    app.register_blueprint(event_tags_blueprint, url_prefix="/api/tag")
    app.register_blueprint(event_dates_blueprint, url_prefix="/api/date")
    app.register_blueprint(events_blueprint, url_prefix="/api/event")
    app.register_blueprint(locations_blueprint, url_prefix="/api/location")
    app.register_blueprint(users_blueprint, url_prefix="/api/user")
    # app.register_blueprint(event_contribution_blueprint,
    # url_prefix="/api/contribution")
    # app.register_blueprint(favorites_blueprint, url_prefix="/api/favorites")
    app.register_blueprint(activity_blueprint, url_prefix="/api/activity")


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

    extensions.apidocs.register(LoginResource, "auth.LoginResource")
    extensions.apidocs.register(LogoutResource, "auth.LogoutResource")
    extensions.apidocs.register(UsersResource, "users.UsersResource")
    extensions.apidocs.register(TagsResource, "tags.TagsResource")
    extensions.apidocs.register(PointsResource, "locations.PointsResource")
    extensions.apidocs.register(LocationResource, "locations.LocationResource")
    extensions.apidocs.register(LocationsResource, "locations.LocationsResource")
    extensions.apidocs.register(DateResource, "dates.DateResource")
    extensions.apidocs.register(DatesResource, "dates.DatesResource")
    extensions.apidocs.register(EventDatesResource, "dates.EventDatesResource")
    extensions.apidocs.register(EventResource, "events.EventResource")
    extensions.apidocs.register(EventsResource, "events.EventsResource")


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
    response = jsonify(InvalidRoute(message={"new_url": error.new_url}).to_dict())
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
