from .model import User
from pmapi import validate
import pmapi.exceptions as exc


def get_user(user_identifier):
    """Query the db for a user. Identifier may be an email, or username.
    """
    search_property = "username"
    # identifier is uuid?
    try:
        validate.uuid(user_identifier)
        search_property = "id"
    except exc.InvalidAPIRequest:
        pass
    # identifier is email?
    if "@" in user_identifier:
        search_property = "email"

    user = User.query.filter(
        getattr(User, search_property) == user_identifier).first()
    return user, search_property


def get_user_or_404(user_identifier):
    """Return a user or raise 404 exception"""
    user, search_property = get_user(user_identifier.lower())
    if not user:
        msg = "No such user with {} {}".format(
            search_property, user_identifier)
        raise exc.RecordNotFound(msg)

    return user
