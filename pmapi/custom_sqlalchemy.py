from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import scoped_session, sessionmaker
from contextlib import contextmanager
from flask import g

class CustomSQLAlchemy(SQLAlchemy):
    def __init__(self, *args, **kwargs):
        super(CustomSQLAlchemy, self).__init__(*args, **kwargs)
        self._scoped_session_factory = None

    def init_app(self, app):
        super(CustomSQLAlchemy, self).init_app(app)
        # Create a scoped session factory for Celery tasks
        self._scoped_session_factory = scoped_session(sessionmaker(bind=self.engine))

    def get_session(self):
        # Use a scoped session for Celery tasks; otherwise, use the default session
        if hasattr(g, 'celery_task'):
            return self._scoped_session_factory()
        else:
            return super(CustomSQLAlchemy, self).session

    def remove(self):
        # Remove the scoped session if it exists
        if hasattr(g, 'celery_task'):
            self._scoped_session_factory.remo