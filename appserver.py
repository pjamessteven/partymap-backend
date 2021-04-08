from pmapi.config import BaseConfig

"""
appserver.py
- creates an application instance and runs the dev server
"""

if __name__ == "__main__":
    from pmapi.application import create_app

    app = create_app(BaseConfig)
    app.run(host="0.0.0.0")
