from flask_caching import Cache
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_login import LoginManager
from pmapi.custom_sqlalchemy import CustomSQLAlchemy

from sqlalchemy_continuum.plugins import ActivityPlugin, FlaskPlugin
from pmapi.mail import Mailer
from flask_apispec import FlaskApiSpec
from flask_track_usage import TrackUsage
from pmapi.config import BaseConfig
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from celery import Celery
from flask_babel import Babel
from flask.helpers import get_debug_flag
from flask import current_app

DEV_ENVIRON = get_debug_flag()

class ContextTask(Celery.Task):
    """An abstract Celery Task that ensures that the connection the the
    database is closed on task completion"""
    abstract = True

    def __call__(self, *args, **kwargs):
        with current_app.app_context():
            return super().__call__(*args, **kwargs)
        
    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        db.session.remove()


allowed_origins = [
    "http://localhost:9000",
    "https://partymap.com"
] if DEV_ENVIRON else [ "https://partymap.com"]

cache = Cache(config={"CACHE_TYPE": "simple"})
admin = Admin(name="PARTYMAP", template_mode="bootstrap3")
db = CustomSQLAlchemy()
cors = CORS(resources={r"/api/*": {"origins": allowed_origins, "supports_credentials": True}})
lm = LoginManager()
activity_plugin = ActivityPlugin()
flask_plugin = FlaskPlugin()
mail = Mailer()
apidocs = FlaskApiSpec()
tracker = TrackUsage()
celery = Celery(
    __name__,
    task_cls=ContextTask
)
engine = create_engine(BaseConfig.SQLALCHEMY_DATABASE_URI, 
            pool_size=4,  # Match with celery concurrency
            max_overflow=0  # Prevent excessive connections
        )
Session = sessionmaker(engine)  # import when you want to manually create a session
babel = Babel()


def configure_celery(app, celery):
    celery.config_from_object('celeryconfig')
    return celery


def get_locale():
    # if a user is logged in, use the locale from the user settings
    user = getattr(g, 'user', None)
    if user is not None:
        return user.locale
    # otherwise try to guess the language from the user accept
    # header the browser transmits.  We support de/fr/en in this
    # example.  The best match wins.
    return request.accept_languages.best_match(['de', 'fr', 'en'])

