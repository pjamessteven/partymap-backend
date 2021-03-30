"""
application.py
- creates a Flask app instance and registers the database object
"""

from flask import Flask
from flask import current_app
from flask_cors import cross_origin
from sqlalchemy import func
from geoalchemy2 import Geometry
from flask_dance.contrib.facebook import make_facebook_blueprint, facebook
from flask_dance.consumer.storage.sqla import SQLAlchemyStorage
from sqlalchemy_continuum import make_versioned
from flask_login import current_user
from datetime import datetime

from pmapi import extensions

import os
# ONLY FOR TESTING !!
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


def create_app(app_name='PARTYMAP'):
    app = Flask(app_name)
    app.config.from_object('pmapi.config.BaseConfig')

    register_extensions(app)
    register_blueprints(app)

    @app.before_request
    def update_last_active():
        if current_user.is_authenticated:
            current_user.last_active = datetime.utcnow()
            extensions.db.session.add(current_user)
            extensions.db.session.commit()

    # potential security risk?
    @app.route('/<path:path>')
    @cross_origin()
    def static_file(path):
        print('test')
        return app.send_static_file(path)

    return app


def register_extensions(app):
    extensions.cache.init_app(app)
    extensions.db.init_app(app)
    extensions.admin.init_app(app)
    extensions.lm.init_app(app)
    extensions.cors.init_app(app)
    extensions.lm.login_view = 'api.login'


def register_blueprints(app):
    # from pmapi.auth.oauth_resource import oauth_blueprint
    from pmapi.auth.resource import auth_blueprint
    from pmapi.event_tag.resource import event_tags_blueprint
    from pmapi.event_date.resource import event_dates_blueprint
    from pmapi.event.resource import events_blueprint
    from pmapi.event_location.resource import locations_blueprint
    from pmapi.user.resource import users_blueprint
    from pmapi.event_contribution.resource import event_contribution_blueprint
    from pmapi.report.resource import report_blueprint
    from pmapi.favorite_events.resource import favorites_blueprint
    from pmapi.activity.resource import activity_blueprint

    # app.register_blueprint(oauth_blueprint, url_prefix="/api/oauth")
    app.register_blueprint(auth_blueprint, url_prefix="/api/auth")
    app.register_blueprint(event_tags_blueprint, url_prefix="/api/event_tags")
    app.register_blueprint(event_dates_blueprint, url_prefix="/api/event_date")
    app.register_blueprint(events_blueprint, url_prefix="/api/event")
    app.register_blueprint(locations_blueprint, url_prefix="/api/locations")
    app.register_blueprint(users_blueprint, url_prefix="/api/users")
    app.register_blueprint(event_contribution_blueprint, url_prefix="/api/contribution")
    app.register_blueprint(report_blueprint, url_prefix="/api/report")
    app.register_blueprint(favorites_blueprint, url_prefix="/api/favorites")
    app.register_blueprint(activity_blueprint, url_prefix="/api/activity")
