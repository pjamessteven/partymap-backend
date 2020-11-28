"""
application.py
- creates a Flask app instance and registers the database object
"""

from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin
from flask_cors import CORS, cross_origin
from flask import current_app

db = SQLAlchemy()
lm = LoginManager()

def create_app(app_name='PARTYMAP'):
    app = Flask(app_name)
    app.config.from_object('pmapi.config.BaseConfig')

    #Cross Origin Resource Sharing
    cors = CORS(app, resources={r"/api/*": {"origins": "*", "supports_credentials": True}})

    from pmapi.api import api
    app.register_blueprint(api, url_prefix="/api")

    db.init_app(app)

    lm.init_app(app)
    lm.login_view = 'api.login'


    return app
