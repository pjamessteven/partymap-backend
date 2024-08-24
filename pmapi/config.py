"""
config.py
- settings for the flask application object
"""
import os


class BaseConfig(object):
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", "postgresql:///partymap")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # used for encryption and session management
    SECRET_KEY = os.getenv("SECRET_KEY")
    CELERY_RESULT_BACKEND = "rpc://"
    CELERY_BROKER_URL = "pyamqp://guest@localhost"
    TOP_LEVEL_DIR = os.path.abspath(os.curdir)

    SENDGRID_DEFAULT_FROM = "noreply@partymap.com"
    SUPPORT_EMAIL = "info@partymap.com"
    LOGIN_REDIRECT_URL = "http://localhost:8080/login"
    
    TRACK_USAGE_USE_FREEGEOIP = True
    TRACK_USAGE_INCLUDE_OR_EXCLUDE_VIEWS = "include"  # include all views
    TRACK_USAGE_COOKIE = True

    ANON_USER_ID = "ac858dc2-2018-4de2-9975-3d716030eb72"
    SYSTEM_USER_ID = "803bbeba-0c37-47fd-a218-969774d54c5d"

    FACEBOOK_OAUTH_CLIENT_ID = os.getenv("FACEBOOK_OAUTH_CLIENT_ID")
    FACEBOOK_OAUTH_CLIENT_SECRET = os.getenv("FACEBOOK_OAUTH_CLIENT_SECRET")

    GOOGLE_OAUTH_CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
    GOOGLE_OAUTH_CLIENT_SECRET = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")

    HCPATCHA_KEY = os.getenv("HCPATCHA_KEY")
    SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
    LAST_FM_API_KEY = os.getenv("LAST_FM_API_KEY")
    SPOTIFY_API_KEY = os.getenv("SPOTIFY_API_KEY")
    SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")

    TRACK_USAGE_FREEGEOIP_ENDPOINT = (
        "http://extreme-ip-lookup.com/json/{ip}?key=" + os.getenv("EXTREME_IP_LOOKUP_KEY")
    )

    # This indicates that it's OK for Google to return different OAuth scopes than requested; Google does that sometimes.
    OAUTHLIB_RELAX_TOKEN_SCOPE = True


class DevConfig(BaseConfig):
    DEBUG = True
    CELERY_BROKER_URL = "amqp://%s:%s@%s" % (os.getenv("RABBITMQ_DEFAULT_USER", ""), os.getenv(
        "RABBITMQ_DEFAULT_PASS", ""), os.getenv("RABBIT_MQ_HOSTNAME", ""))

    # Uploads
    TOP_LEVEL_DIR = os.path.abspath(os.curdir)
    MEDIA_UPLOAD_FOLDER = TOP_LEVEL_DIR + "/static/uploaded_media/"
    WEBSITE_URL = "http://localhost:9000"
    UPLOADS_URL = "http://localhost:5000/uploaded_media/"

    LOGIN_REDIRECT_URL = "http://localhost:9000/login"

    # This indicates that you're doing local testing, and it's OK to use HTTP instead of HTTPS for OAuth.
    OAUTHLIB_INSECURE_TRANSPORT = True
    TRACK_USAGE_USE_FREEGEOIP = False


class ProdConfig(BaseConfig):
    DEBUG = False

    CELERY_RESULT_BACKEND = "rpc://"
    CELERY_BROKER_URL = "pyamqp://guest@localhost"

    # Uploads
    MEDIA_UPLOAD_FOLDER = "/var/www/content.partymap.com/uploaded_media/"
    WEBSITE_URL = "https://partymap.com"
    UPLOADS_URL = "https://content.partymap.com/uploaded_media/"

    LOGIN_REDIRECT_URL = "https://partymap.com/login"
