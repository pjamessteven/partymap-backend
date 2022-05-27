from pmapi.exceptions import InvalidAPIRequest
from uuid import UUID
from flask import current_app
from pmapi.utils import ROLES
from pmapi.utils import ACCOUNT_STATUSES
import re

PASSWORD_LENGTH_MIN = 8
PASSWORD_LENGTH_MAX = 72  # changeme


def username(username):
    """Character limit: 3-25 chars
    Alpha-numeric, hyphen , underscore (_)
    No international characters
    All characters MUST be lowercase.
    username can't start with "q_"
    """
    if len(username) > 25:
        raise InvalidAPIRequest("Username must not be longer than 25 characters")
    if len(username) < 3:
        raise InvalidAPIRequest("Username must be 3 characters or more")
    if not re.match("[0-9a-z_-]+$", username):
        raise InvalidAPIRequest(
            "Username may only contain lower case alphanumeric, '-', or '_'"
        )

    return True


def role(role):
    if not isinstance(role, int):
        raise InvalidAPIRequest("Role must be a number")
    if role not in list(ROLES.values()):
        raise InvalidAPIRequest("Role does not exist")
    return True


def status(status):
    if status not in ACCOUNT_STATUSES:
        raise InvalidAPIRequest("Status is not valid")
    return True


def email(email):
    if not re.match("[^@ ]+@[^@ ]+\.[^@ ]+", email):
        raise InvalidAPIRequest('Invalid email addess "{}"'.format(email))
    return True


def uuid(uuid, err_msg=None):
    """Raise an error if 'uuid' does not look like a valid UUID"""
    if isinstance(uuid, UUID):
        return True
    try:
        UUID(uuid)
        return True
    except (ValueError, TypeError):
        raise InvalidAPIRequest(err_msg or '"{}" is not a valid UUID'.format(uuid))


def password(password):
    """Minimum 8 chars
    Maximum 72 chars
    all characters allowed
    """
    if (
        not password
        or len(password) < PASSWORD_LENGTH_MIN
        or len(password) > PASSWORD_LENGTH_MAX
    ):

        msg = "Password must be between {min} and {max} characters long".format(
            min=PASSWORD_LENGTH_MIN, max=PASSWORD_LENGTH_MAX
        )
        raise InvalidAPIRequest(msg)

    return True
