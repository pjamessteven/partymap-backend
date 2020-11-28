from pmapi.exceptions import InvalidAPIRequest
from uuid import UUID
from flask import current_app

PASSWORD_LENGTH_MIN = 5
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
    if username.startswith("q_"):
        raise InvalidAPIRequest("Usernames starting with 'q_' are reserved")
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
    """Minimum 5 chars
    Maximum 72 chars
    all characters allowed
    """
    if not password or \
       len(password) < PASSWORD_LENGTH_MIN or \
       len(password) > PASSWORD_LENGTH_MAX:

        msg = "Password must be between {min} and {max} characters long"\
            .format(min=PASSWORD_LENGTH_MIN, max=PASSWORD_LENGTH_MAX)
        raise InvalidAPIRequest(msg)

    return True


def allowed_file(extension):
    if not '.' in extension and \
           extension.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']:
        msg = "File must be of one of the following formats:  {0}".format(
            current_app.config['ALLOWED_EXTENSIONS'])
        raise InvalidAPIRequest(msg)

    return True
