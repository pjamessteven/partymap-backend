from flask import url_for
from pmapi.notification.model import EmailAction
from sqlalchemy import and_


def test_create_user_with_valid_token(anon_user, db):
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
    rv = anon_user.client.post(url_for("users.UsersResource"), json=user_args)
    assert rv.status_code == 200


def test_create_user_with_invalid_token(anon_user):
    user_args = {
        "username": "new_user",
        "email": "test@example.com",
        "activate": True,
        "password": "12345678",
        "token": "123",
    }

    rv = anon_user.client.post(url_for("users.UsersResource"), json=user_args)
    assert rv.status_code == 404


def test_create_user_with_no_token(anon_user):
    user_args = {
        "username": "new_user",
        "email": "test@example.com",
        "activate": True,
        "password": "12345678",
    }

    rv = anon_user.client.post(url_for("users.UsersResource"), json=user_args)
    assert rv.status_code == 404


def test_create_user_fails_with_dupe_email(admin_user, anon_user, db):
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

    rv = anon_user.client.post(url_for("users.UsersResource"), json=user_args)
    assert rv.status_code == 409


def test_create_user_fails_with_dupe_name(admin_user, anon_user, db):
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

    rv = anon_user.client.post(url_for("users.UsersResource"), json=user_args)
    assert rv.status_code == 409


def test_activate_user(anon_user, db):
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

    # create user
    rv = anon_user.client.post(url_for("users.UsersResource"), json=user_args)
    assert rv.status_code == 200

    user_id = rv.json.get("id")
    # find activate token from db
    email_verify_action = (
        db.session.query(EmailAction)
        .filter(
            and_(EmailAction.action == "email_verify", EmailAction.user_id == user_id)
        )
        .first()
    )

    rv = anon_user.client.post(url_for("users.activate", token=email_verify_action.id))
    assert rv.status_code == 200


def test_activate_user_invalid_token(anon_user, db):
    rv = anon_user.client.post(url_for("users.activate", token="test"))
    assert rv.status_code == 404
