from sqlalchemy import or_
from flask_login import current_user, logout_user
from werkzeug.security import generate_password_hash
from sqlalchemy_continuum import versioning_manager
from .model import User, OAuth
from pmapi import validate
import pmapi.exceptions as exc
from pmapi.common.controllers import paginated_results
from pmapi.notification.model import EmailAction
from pmapi.mail.controllers import (
    send_signup_verify_email,
    send_change_email_address_email,
    send_password_reset_email,
)
from pmapi.utils import ROLES
from pmapi.extensions import db
import pmapi.event.controllers as events
from pmapi.event.model import event_page_views_table, user_event_following_table
from pmapi.event_date.model import user_event_date_going_table, user_event_date_interested_table
import pmapi.media_item.controllers as media_items
from flask_login import (
    login_user,
)
from flask import session

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

    user = User.query.filter(
        getattr(User, search_property) == user_identifier).first()
    return user, search_property


def get_user_by_email(email):
    """Query the db for a user. Identifier may be an email, or username."""

    user = User.query.filter(
        User.email == email).first()
    return user


def get_user_by_one_off_token(token):
    """Query the db for a user. Identifier may be an email, or username."""

    user = User.query.filter(
        User.one_off_auth_token == token).first()

    return user


def get_user_or_404(user_identifier):
    """Return a user or raise 404 exception"""
    user, search_property = get_user(user_identifier)
    if not user:
        msg = "No such user with {} {}".format(
            search_property, user_identifier)
        raise exc.RecordNotFound(msg)

    return user


def get_user_by_token_or_404(user_identifier):
    """Return a user or raise 404 exception"""
    user = get_user_by_one_off_token(user_identifier)
    if not user:
        msg = "No such user with token {}".format(
            user_identifier)
        raise exc.RecordNotFound(msg)

    return user


def get_users(**kwargs):
    query = db.session.query(User)

    if kwargs.get("query", None) is not None:
        query_string = "%{}%".format(kwargs.pop("query"))
        search_property = "username"
        # identifier is uuid?
        try:
            validate.uuid(query_string)
            search_property = "id"
        except exc.InvalidAPIRequest:
            pass
        # identifier is email?
        if "@" in query_string:
            search_property = "email"
        query = User.query.filter(
            getattr(User, search_property).ilike(query_string))

    if kwargs.get("status", None) is not None:
        status = kwargs.pop("status")
        query = query.filter(User.status == status)

    if kwargs.get("role", None) is not None:
        role = kwargs.pop("role")
        query = query.filter(User.role == role)

    return paginated_results(User, query=query, **kwargs)


def check_user_does_not_exist(username, email):
    existing_user = User.query.filter(
        or_(User.username == username, User.email == email)
    ).first()
    if existing_user:
        if existing_user.username == username:
            raise exc.RecordAlreadyExists(code="USERNAME_TAKEN")
        else:
            raise exc.RecordAlreadyExists(code="EMAIL_ALREADY_REGISTERED")


def check_email_not_registered(email):
    existing_user = User.query.filter(User.email == email).first()
    if existing_user:
        raise exc.RecordAlreadyExists(code="EMAIL_ALREADY_REGISTERED")


def create_user(**kwargs):
    activate = kwargs.pop("activate", None)
    username = kwargs.pop("username", None)
    email = kwargs.pop("email", None)
    password = kwargs.pop("password", None)
    role = kwargs.pop("role", 0)

    # all user created with token will have role=10
    token = kwargs.pop("token", None)
    if token:
        email_action = EmailAction.query.get(token)

        # must be staff to add user without
        if not email_action:
            if not current_user or not current_user.is_authenticated:
                raise exc.RecordNotFound(
                    "Invitation code is required to sign up.")
            elif current_user.is_authenticated and current_user.role < ROLES["STAFF"]:
                raise exc.RecordNotFound(
                    "Invitation code is required to sign up.")
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
    user = User(email=email, username=username, role=role)

    db.session.add(user)
    db.session.commit()

    user.set_password(password)
    print(user)

    if activate:
        user.activate()
    else:
        # send activation email to user
        email_action = EmailAction(user=user, action="email_verify")
        db.session.add(email_action)
        db.session.commit()
        send_signup_verify_email(user, email_action.id)

    logging.info(
        "user.create",
        id=user.id,
        username=user.username,
        email=user.email,
        status=user.status,
    )

    db.session.commit()
    user, search_property = get_user(email)
    return user


def activate_user(token):
    """Activate a user using the EmailAction id that was emailed to the user"""
    email_action = EmailAction.query.get(token)
    if not email_action:
        # token not found
        raise exc.RecordNotFound("No such token ({})".format(token))
    if email_action.actioned:
        # account already activated
        raise exc.InvalidAPIRequest("Your account has already been activated!")
    else:
        # activate user
        user = email_action.user
        user.activate()
        email_action.actioned = True
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
    role = kwargs.pop("role", None)
    status = kwargs.pop("status", None)
    avatar = kwargs.pop("avatar", None)
    alias = kwargs.pop("alias", None)
    description = kwargs.pop("description", None)

    user = get_user_or_404(user_id)

    if username:
        # check username doesn't exist
        check_user_does_not_exist(username, email)
        validate.username(username)
        user.username = username

    if alias:
        validate.user_alias(alias)
        user.alias = alias

    if description:
        validate.user_description(description)
        user.description = description

    if avatar:
        media_item = media_items.upload_user_avatar(
            avatar,  user=user, creator=current_user)
        user.avatar = media_item

    if password:
        validate.password(password)
        if password != password_confirm:
            raise exc.InvalidAPIRequest("Passwords don't match")
        user.set_password(password)

    if email:
        validate.email(email)
        check_email_not_registered(email)
        if current_user.role < ROLES["STAFF"]:
            # send verification email to user
            email_action = EmailAction(
                user=user, action="email_verify", extra_data=email
            )
            db.session.add(email_action)
            db.session.commit()
            send_change_email_address_email(user, email_action.id)
        else:
            # staff users can update email addresses without verification
            user.email = email

    if role:
        role = int(role)
        if current_user.role < ROLES["ADMIN"]:
            raise exc.InvalidPermissions("Only admin can update user role")
        validate.role(role)
        user.role = role

    if status:
        if current_user.role < ROLES["STAFF"]:
            raise exc.InvalidPermissions("Only staff can update user status")
        validate.status(status)
        user.status = status

    db.session.commit()
    return user


def delete_user(user_id):
    user = get_user_or_404(user_id)
    # delete oauth token
    if user.oauth:
        token = OAuth.query.filter(OAuth.user_id == user_id).first()
        db.session.delete(token)

    if user.created_events:
        for event in user.created_events:
            events.delete_event(event.id)

    if user.created_suggestions:
        for suggestion in user.created_suggestions:
            db.session.delete(suggestion)

    if user.created_contributions:
        for contribution in user.created_contributions:
            db.session.delete(contribution)

    user.avatar = None

    db.session.flush()

    if user.created_media_items:
        for media_item in user.created_media_items:
            db.session.delete(media_item)

    delete_following = user_event_following_table.delete().where(
        user_event_following_table.c.user_id == user.id)

    delete_going = user_event_date_going_table.delete().where(
        user_event_following_table.c.user_id == user.id)

    delete_interested = user_event_date_interested_table.delete().where(
        user_event_following_table.c.user_id == user.id)

    delete_page_views = event_page_views_table.delete().where(
        event_page_views_table.c.user_id == user.id)

    db.session.execute(delete_following)
    db.session.execute(delete_going)
    db.session.execute(delete_interested)
    db.session.execute(delete_page_views)

    #Transaction = versioning_manager.transaction_cls
    # transactions = db.session.query(Transaction).filter(
    #    Transaction.user_id == user.id)
    # for transaction in transactions:
    #    db.session.delete(transaction)

    # can't fully delete user without deleting transactions which
    # we shouldnt do as we lose track of what is an important changelog
    user.username = None
    user.email = None
    user.password = None

    db.session.commit()

    logout_user()

    return


def request_password_reset(identifier):
    user = get_user_or_404(identifier)
    # send activation email to user
    email_action = EmailAction(user=user, action="password_reset")
    db.session.add(email_action)
    db.session.commit()
    send_password_reset_email(user, email_action.id)
    return


def reset_password(token, password, password_confirm):
    """ Reset user password using the EmailAction id that was emailed to the user"""
    email_action = EmailAction.query.get(token)
    if not email_action:
        raise exc.RecordNotFound("No such token ({})".format(token))
    user = email_action.user

    validate.password(password)
    if password != password_confirm:
        raise exc.InvalidAPIRequest("Passwords don't match")
    user.set_password(password)
    # reset password attempts
    session["attempt"] = 5

    db.session.delete(email_action)
    db.session.commit()

    # flask-login
    login_user(user, remember=True)

    return user
