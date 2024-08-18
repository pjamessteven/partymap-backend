import pytest
import datetime
from sqlalchemy import and_

from pmapi.user.model import User
from pmapi.notification.model import EmailAction
import pmapi.user.controllers as users
from pmapi.extensions import mail


from pmapi.exceptions import InvalidAPIRequest
from pmapi.exceptions import InvalidPermissions
from pmapi.exceptions import RecordAlreadyExists
from pmapi.exceptions import RecordNotFound


def test_get_all_users(admin_user):
    all_users = users.get_all_users()
    assert all_users.total >= 1
    assert admin_user in all_users.items
