from flask_caching import Cache
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_login import LoginManager
from sqlalchemy_continuum.plugins import ActivityPlugin, FlaskPlugin
from pmapi.mail import Mailer
from flask_apispec import FlaskApiSpec
from flask_track_usage import TrackUsage
from pmapi.config import BaseConfig
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

cache = Cache(config={"CACHE_TYPE": "simple"})
admin = Admin(name="PARTYMAP", template_mode="bootstrap3")
db = SQLAlchemy()
cors = CORS(resources={r"/api/*": {"origins": "*", "supports_credentials": True}})
lm = LoginManager()
activity_plugin = ActivityPlugin()
flask_plugin = FlaskPlugin()
mail = Mailer()
apidocs = FlaskApiSpec()
tracker = TrackUsage()

engine = create_engine(BaseConfig.SQLALCHEMY_DATABASE_URI)
Session = sessionmaker(engine)  # import when you want to manually create a session
