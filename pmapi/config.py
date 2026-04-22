"""
config.py
- settings for the flask application object
"""

import os


class BaseConfig(object):
    SESSION_COOKIE_SAMESITE = None

    WEBSITE_URL = os.getenv("WEBSITE_URL")
    UPLOADS_URL = os.getenv("UPLOADS_URL")
    LOGIN_REDIRECT_URL = os.getenv("WEBSITE_URL") + "/login"

    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "postgresql:///partymap")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # used for encryption and session management
    SECRET_KEY = os.getenv("SECRET_KEY")

    TOP_LEVEL_DIR = os.path.abspath(os.curdir)

    SENDGRID_DEFAULT_FROM = "noreply@partymap.com"
    SUPPORT_EMAIL = "info@partymap.com"

    TRACK_USAGE_USE_FREEGEOIP = False
    TRACK_USAGE_INCLUDE_OR_EXCLUDE_VIEWS = "include"  # include all views

    ANON_USER_ID = "ac858dc2-2018-4de2-9975-3d716030eb72"
    SYSTEM_USER_ID = "803bbeba-0c37-47fd-a218-969774d54c5d"

    FACEBOOK_OAUTH_CLIENT_ID = os.getenv("FACEBOOK_OAUTH_CLIENT_ID")
    FACEBOOK_OAUTH_CLIENT_SECRET = os.getenv("FACEBOOK_OAUTH_CLIENT_SECRET")

    GOOGLE_OAUTH_CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
    GOOGLE_OAUTH_CLIENT_SECRET = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")

    HCPATCHA_KEY = os.getenv("HCPATCHA_KEY")
    LAST_FM_API_KEY = os.getenv("LAST_FM_API_KEY")
    SPOTIFY_API_KEY = os.getenv("SPOTIFY_API_KEY")
    SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
    GMAPS_API_KEY = os.getenv("GMAPS_API_KEY")

    # This indicates that it's OK for Google to return different OAuth scopes than requested; Google does that sometimes.
    OAUTHLIB_RELAX_TOKEN_SCOPE = True

    MEDIA_UPLOAD_FOLDER = TOP_LEVEL_DIR + "/static/uploaded_media/"

    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    ENABLE_TRANSLATIONS = os.getenv("ENABLE_TRANSLATIONS", "false").lower() == "true"
    ENABLE_EVENT_EMBEDDINGS = (
        os.getenv("ENABLE_EVENT_EMBEDDINGS", "false").lower() == "true"
    )
    EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY") or os.getenv("OPENAI_API_KEY")
    EMBEDDING_API_URL = os.getenv(
        "EMBEDDING_API_URL", "https://api.openai.com/v1/embeddings"
    )
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    EVENT_EMBEDDING_DIMENSIONS = int(os.getenv("EVENT_EMBEDDING_DIMENSIONS", "1536"))
    EVENT_SEARCH_VECTOR_MAX_DISTANCE = float(
        os.getenv("EVENT_SEARCH_VECTOR_MAX_DISTANCE", "0.45")
    )
    EVENT_SEARCH_TEXT_WEIGHT = float(os.getenv("EVENT_SEARCH_TEXT_WEIGHT", "0.35"))
    EVENT_SEARCH_VECTOR_WEIGHT = float(os.getenv("EVENT_SEARCH_VECTOR_WEIGHT", "0.65"))

    ZOHO_CLIENT_ID = os.environ.get("ZOHO_CLIENT_ID")
    ZOHO_CLIENT_SECRET = os.environ.get("ZOHO_CLIENT_SECRET")
    ZOHO_ACCOUNT_ID = os.environ.get("ZOHO_ACCOUNT_ID")

    AGENT_API_KEY = os.environ.get("AGENT_API_KEY")


class DevConfig(BaseConfig):
    DEBUG = True

    # This indicates that you're doing local testing, and it's OK to use HTTP instead of HTTPS for OAuth.
    OAUTHLIB_INSECURE_TRANSPORT = True


class ProdConfig(BaseConfig):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
