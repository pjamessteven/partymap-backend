from flask.helpers import get_debug_flag

from .config import DevConfig
from .config import ProdConfig

CONFIG = DevConfig if get_debug_flag() else ProdConfig

"""
appserver.py
- creates an application instance and runs the dev server
"""

if __name__ == "__main__":
    from pmapi.application import create_app

    app = create_app(CONFIG)
    app.run(host="0.0.0.0")
