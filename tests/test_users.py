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


def test_get_user_gets_by_id(admin_user):
    user, search_property = users.get_user(admin_user.id)
    assert user.id == admin_user.id
    assert search_property == "id"


def test_get_user_gets_by_email(admin_user):
    user, search_property = users.get_user(admin_user.email)
    assert user.id == admin_user.id
    assert search_property == "email"


def test_get_user_or_404_returns_existing(admin_user):
    user = users.get_user_or_404(admin_user.id)
    assert user.id == admin_user.id


def test_get_user_or_404_raises_RecordNotFound(db):
    with pytest.raises(RecordNotFound):
        users.get_user_or_404("some_username")


def test_create_user_with_token_valid_token(db):
    # create token
    token = EmailAction(action="account_create")
    db.session.add(token)
    db.session.commit()

    user_args = {
        "username": "new_user",
        "email": "test@example.com",
        "password": "12345678",
        "token": token.id,
    }

    user = users.create_user_with_token(**user_args)
    assert user.username == user_args.get("username")
    assert user.email == user_args.get("email")
    assert user.active is False


def test_create_user_with_token_invalid_token():
    user_args = {
        "username": "new_user",
        "email": "test@example.com",
        "activate": True,
        "password": "12345678",
        "token": "123",
    }

    with pytest.raises(RecordNotFound):
        users.create_user_with_token(**user_args)


def test_create_user_with_token_no_token():
    user_args = {
        "username": "new_user",
        "email": "test@example.com",
        "activate": True,
        "password": "12345678",
    }

    with pytest.raises(RecordNotFound):
        users.create_user_with_token(**user_args)


def test_create_user_fails_with_token_dupe_name(admin_user, db):
    # create token
    token = EmailAction(action="account_create")
    db.session.add(token)
    db.session.commit()

    user_args = {
        "username": admin_user.username,
        "email": "test@example.com",
        "activate": True,
        "password": "12345678",
        "token": token.id,
    }
    with pytest.raises(RecordAlreadyExists):
        users.create_user_with_token(**user_args)


def test_create_user_with_token_fails_dupe_email(admin_user, db):
    # create token
    token = EmailAction(action="account_create")
    db.session.add(token)
    db.session.commit()

    user_args = {
        "username": "new_user",
        "email": admin_user.email,
        "activate": True,
        "password": "12345678",
        "token": token.id,
    }
    with pytest.raises(RecordAlreadyExists):
        users.create_user(**user_args)


def test_activate_user(db):
    # create sign up token
    token = EmailAction(action="account_create")
    db.session.add(token)
    db.session.commit()

    user_args = {
        "username": "new_user",
        "email": "test@example.com",
        "activate": False,
        "password": "12345678",
        "token": token.id,
    }

    user = users.create_user_with_token(**user_args)

    # find activate token from db
    email_verify_action = (
        db.session.query(EmailAction)
        .filter(
            and_(EmailAction.action == "email_verify", EmailAction.user_id == user.id)
        )
        .first()
    )
    # activate user
    users.activate_user(email_verify_action.id)
    assert user.status == "active"


def test_activate_user_invalid_token(db):

    with pytest.raises(RecordNotFound):
        users.activate_user("12345678")


def test_confirmation_email_sent_to_pending_user(db, emailer):
    # create token
    token = EmailAction(action="account_create")
    db.session.add(token)
    db.session.commit()

    user_args = {
        "username": "new_user",
        "email": "test@example.com",
        "password": "12345678",
        "token": token.id,
    }

    pending_user = users.create_user_with_token(**user_args)
    assert emailer.mail_sent == 1
    assert pending_user.status == "pending"
