from sqlalchemy import or_
from flask_login import current_user
from werkzeug.security import generate_password_hash

from .model import User
from pmapi import validate
import pmapi.exceptions as exc
from pmapi.common.controllers import paginated_results
from pmapi.notification.model import EmailAction
from pmapi.mail.controllers import (
    send_signup_verify_email,
    send_change_email_address_email,
)
from pmapi.utils import ROLES
from pmapi.extensions import db
import logging


def get_all_users(**kwargs):
    return paginated_results(User, **kwargs)


def get_user(user_identifier):
    """Query the db for a user. Identifier may be an email, or username."""
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

    user = User.query.filter(getattr(User, search_property) == user_identifier).first()
    return user, search_property


def get_user_or_404(user_identifier):
    """Return a user or raise 404 exception"""
    user, search_property = get_user(user_identifier.lower())
    if not user:
        msg = "No such user with {} {}".format(search_property, user_identifier)
        raise exc.RecordNotFound(msg)

    return user


def check_user_does_not_exist(username, email):
    existing_user = User.query.filter(
        or_(User.username == username, User.email == email)
    ).first()
    if existing_user:
        if existing_user.username == username:
            raise exc.RecordAlreadyExists(code="USERNAME_TAKEN")
        else:
            raise exc.RecordAlreadyExists(code="EMAIL_ALREADY_REGISTERED")


def create_user(**kwargs):
    activate = kwargs.pop("activate", None)
    username = kwargs.pop("username", None)
    email = kwargs.pop("email", None)
    password = kwargs.pop("password", None)
    role = kwargs.pop("role", 0)

    # all user created with token will have role=10
    # these are priviledged users who can create events
    token = kwargs.pop("token", None)
    if token:
        email_action = EmailAction.query.get(token)

        # must be staff to add user without
        if not email_action:
            if not current_user or not current_user.is_authenticated:
                raise exc.RecordNotFound("Invitation code is required to sign up.")
            elif current_user.is_authenticated and current_user.role < ROLES["STAFF"]:
                raise exc.RecordNotFound("Invitation code is required to sign up.")
        else:
            if email_action.expired:
                # token has expired (5 minutes passed)
                db.session.delete(email_action)
                db.session.flush()
                raise exc.RecordNotFound("confirmation token has expired")
            db.session.delete(email_action)
            db.session.flush()

        role = 10

    validate.username(username)
    validate.email(email)
    validate.password(password)

    try:
        check_user_does_not_exist(username, email)

    except exc.RecordAlreadyExists as e:
        logging.info("user.create.failed", error=str(e))
        raise e

    # create user
    user = User(email, username, password, role)

    if activate:
        user.activate()
    else:
        # send activation email to user
        email_action = EmailAction(user=user, action="email_verify")
        db.session.add(email_action)
        db.session.flush()
        send_signup_verify_email(user, email_action.id)

    logging.info(
        "user.create",
        id=user.id,
        username=user.username,
        email=user.email,
        status=user.status,
    )

    db.session.add(user)
    db.session.commit()
    return user


def activate_user(token):
    """Activate a user using the EmailAction id that was emailed to the user"""
    email_action = EmailAction.query.get(token)
    if not email_action:
        raise exc.RecordNotFound("No such token ({})".format(token))
    user = email_action.user
    user.activate()
    db.session.delete(email_action)
    db.session.commit()
    logging.info("user.activated")
    return user


def confirm_update_email(token):
    """Called after user has clicked the confirmation link in the email sent"""
    email_action = EmailAction.query.get(token)
    if not email_action:
        raise exc.RecordNotFound("No such token ({})".format(token))
    user = email_action.user
    user.email = email_action.extra_data
    db.session.delete(email_action)
    db.session.commit()
    return user


def edit_user(user_id, **kwargs):
    username = kwargs.pop("username", None)
    email = kwargs.pop("email", None)
    password = kwargs.pop("password", None)
    password_confirm = kwargs.pop("password_confirm", None)

    user = get_user_or_404(user_id)

    if username:
        validate.username(username)
        user.username = username

    if password:
        validate.password(password)
        if password != password_confirm:
            raise exc.InvalidAPIRequest("Passwords don't match")
        user.password = generate_password_hash(password, method="sha256")

    if email:
        validate.email(email)
        # send verification email to user
        # save new email address as extra data so it can be retrieved at vfcation
        email_action = EmailAction(user=user, action="email_verify", extra_data=email)
        db.session.add(email_action)
        db.session.flush()
        send_change_email_address_email(user, email_action.id)

    db.session.commit()
    return user
