from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import scoped_session, sessionmaker
from flask import current_app
import threading

"""A custom SQLAlchemy class that uses a scoped session for celery tasks and regular session for main flask app"""
class CustomSQLAlchemy(SQLAlchemy):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._scoped_session_factory = None
        self._celery_task_local = threading.local()

    def init_app(self, app):
        super().init_app(app)
        # Create a scoped session factory for Celery tasks
        self._scoped_session_factory = scoped_session(
            sessionmaker(bind=self.engine)
        )

    def _is_celery_task(self):
        # Use thread-local storage to track Celery task context
        return getattr(self._celery_task_local, 'is_celery_task', False)

    def _set_celery_task_context(self, is_task):
        # Set the Celery task context for the current thread
        self._celery_task_local.is_celery_task = is_task

    def session_factory(self):
        # Determine which session to use based on the current context
        if self._is_celery_task():
            return self._scoped_session_factory()
        return super().session

    def remove(self):
        # Remove the scoped session if it exists
        if self._scoped_session_factory:
            self._scoped_session_factory.remove()