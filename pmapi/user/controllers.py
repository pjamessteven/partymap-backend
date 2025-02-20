from sqlalchemy import or_
from flask_login import current_user, logout_user, login_user
from werkzeug.security import generate_password_hash
from sqlalchemy_continuum import transaction_class
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
from pmapi.event.model import event_page_views_table, user_event_following_table
from pmapi.event_date.model import user_event_date_going_table, user_event_date_interested_table
import pmapi.media_item.controllers as media_items

from flask import session
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import MetaData, Table, Column
import logging

from pmapi.config import BaseConfig
from functools import wraps

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


def check_username_not_taken(username):
    existing_user = User.query.filter(
        User.username == username
    ).first()
    if existing_user:
        raise exc.RecordAlreadyExists(code="USERNAME_TAKEN")


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
    locale = kwargs.pop("locale", None)
    user = get_user_or_404(user_id)

    if username:
        # check username doesn't exist
        check_username_not_taken(username)
        validate.username(username)
        user.username = username

    if alias:
        validate.user_alias(alias)
        user.alias = alias

    if description:
        validate.user_description(description)
        user.description = description

    if avatar:
        if user.avatar:
            media_items.delete_item(user.avatar)

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

    if locale:
        user.locale = locale
        
    db.session.commit()
    return user


def delete_user(user_id):
    user = get_user_or_404(user_id)

    # delete oauth token
    if user.oauth:
        token = OAuth.query.filter(OAuth.user_id == user.id).first()
        if token:
            db.session.delete(token)

    if user.created_events:
        for event in user.created_events:
            if event.host_id == user.id:
                from pmapi.event.controllers import delete_event
                # only delete events that the user is the host of
                delete_event(event.id)
            else:
                # for general events ('an event I know about')
                # dont delete them
                event.creator_id = None

    if user.created_suggestions:
        for suggestion in user.created_suggestions:
            db.session.delete(suggestion)

    if user.created_reviews:
        for review in user.created_reviews:
            db.session.delete(review)

    if user.avatar:
        media_items.delete_item(user.avatar)
        
    if user.created_media_items:
        for media_item in user.created_media_items:
            if media_item.event:
                if media_item.event.host_id == user.id:
                     media_items.delete_item(media_item)
                else:
                    # don't delete media for events where user is not the host
                    # (event posters etc.)
                    media_item.creator_id = None
            else:
                media_items.delete_item(media_item)


    db.session.flush()

    logout_user()

    user.avatar = None
    user.username = None
    user.email = None
    user.password = None
    user.alias = None
    user.description = None

    """
    need to fix this but for now, whatever
    delete_following = user_event_following_table.delete().where(
        user_event_following_table.c.user_id == str(user.id))
    db.session.execute(delete_following)

    delete_going = user_event_date_going_table.delete().where(
        user_event_date_going_table.c.user_id == str(user.id))
    db.session.execute(delete_going)

    delete_interested = user_event_date_interested_table.delete().where(
        user_event_date_interested_table.c.user_id == str(user.id))
    db.session.execute(delete_interested)

    delete_page_views = event_page_views_table.delete().where(
        event_page_views_table.c.user_id == str(user.id))
    db.session.execute(delete_page_views)
    """

    db.session.commit()

    return ("", 201)


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
    user.login_attempts = 0

    db.session.delete(email_action)
    db.session.commit()

    # flask-login
    login_user(user, remember=True)

    return user


# wrapper function for actioning as system user
def action_as_system_user(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try: 
            requesting_user = get_user_or_404(current_user.id)
            system_user = get_user_or_404(BaseConfig.SYSTEM_USER_ID)
            login_user(system_user, force=True)
        except Exception as e:
            print(f"Action as system: Error retrieving users: {str(e)}")
            raise
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            print(f"Action as system: Error occurred: {str(e)}") 
            raise
        finally:
            login_user(requesting_user, remember=True)

        return result
    return wrapper
