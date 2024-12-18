from pmapi.extensions import make_celery, current_app
from pmapi.application import create_app
from .config import DevConfig, ProdConfig
from flask.helpers import get_debug_flag

DEV_ENVIRON = get_debug_flag()
CONFIG = DevConfig if DEV_ENVIRON else ProdConfig

# Create the Flask app
app = current_app if current_app else create_app(CONFIG)

# Initialize Celery with the app
celery = make_celery(app)
