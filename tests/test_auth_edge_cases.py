import pytest
from flask import url_for

import pmapi.auth.controllers as auth
import pmapi.user.controllers as users
from pmapi.user.model import User


# ---------------------------------------------------------------------------
# Login edge cases
# ---------------------------------------------------------------------------


def test_login_with_valid_credentials(regular_user):
    """POST /auth/login with valid credentials should return 200."""
    rv = regular_user.client.post(
        url_for("auth.LoginResource"),
        json={"identifier": regular_user.email, "password": "user_password"},
    )
    assert rv.status_code == 200


def test_login_with_invalid_credentials(anon_user, regular_user):
    """POST /auth/login with wrong password should return 400."""
    rv = anon_user.client.post(
        url_for("auth.LoginResource"),
        json={"identifier": regular_user.email, "password": "wrong_password"},
    )
    assert rv.status_code == 400


def test_login_attempts_increment_on_failure(anon_user, regular_user, db):
    """Failed logins should increment login_attempts."""
    initial = regular_user.login_attempts

    anon_user.client.post(
        url_for("auth.LoginResource"),
        json={"identifier": regular_user.email, "password": "wrong_password"},
    )

    db.session.refresh(regular_user)
    assert regular_user.login_attempts == initial + 1


def test_login_attempts_reset_on_success(regular_user, db):
    """Successful login should reset login_attempts to 0."""
    regular_user.login_attempts = 3
    db.session.commit()

    regular_user.client.post(
        url_for("auth.LoginResource"),
        json={"identifier": regular_user.email, "password": "user_password"},
    )

    db.session.refresh(regular_user)
    assert regular_user.login_attempts == 0


def test_login_disabled_user(anon_user, regular_user, db):
    """Disabled user should not be able to log in."""
    regular_user.status = "disabled"
    db.session.commit()

    rv = anon_user.client.post(
        url_for("auth.LoginResource"),
        json={"identifier": regular_user.email, "password": "user_password"},
    )
    assert rv.status_code == 403


def test_login_pending_user(anon_user, regular_user, db):
    """Pending user should not be able to log in."""
    regular_user.status = "pending"
    db.session.commit()

    rv = anon_user.client.post(
        url_for("auth.LoginResource"),
        json={"identifier": regular_user.email, "password": "user_password"},
    )
    assert rv.status_code == 403


def test_account_locks_after_too_many_attempts(anon_user, regular_user, db):
    """Account should be locked after 5 failed login attempts."""
    regular_user.login_attempts = 4
    db.session.commit()

    # 5th wrong attempt -> now locked
    rv = anon_user.client.post(
        url_for("auth.LoginResource"),
        json={"identifier": regular_user.email, "password": "wrong_password"},
    )
    assert rv.status_code == 400
    db.session.refresh(regular_user)
    assert regular_user.login_attempts == 5
    assert rv.json["error"]["code"] == "ACCOUNT_LOCKED"

    # Subsequent attempts should also be locked
    rv = anon_user.client.post(
        url_for("auth.LoginResource"),
        json={"identifier": regular_user.email, "password": "wrong_password"},
    )
    assert rv.status_code == 400
    assert rv.json["error"]["code"] == "ACCOUNT_LOCKED"


def test_successful_login_resets_lock(anon_user, regular_user, db):
    """After lockout, correct password should still work and reset attempts."""
    regular_user.login_attempts = 5
    db.session.commit()

    rv = anon_user.client.post(
        url_for("auth.LoginResource"),
        json={"identifier": regular_user.email, "password": "user_password"},
    )
    assert rv.status_code == 200
    db.session.refresh(regular_user)
    assert regular_user.login_attempts == 0


# ---------------------------------------------------------------------------
# One-off token login
# ---------------------------------------------------------------------------


def test_login_with_one_off_token(anon_user, regular_user, db):
    """POST /auth/login with a one_off_auth_token should log user in."""
    import uuid
    token = str(uuid.uuid4())
    regular_user.one_off_auth_token = token
    db.session.commit()

    rv = anon_user.client.post(
        url_for("auth.LoginResource"),
        json={"token": token},
    )
    assert rv.status_code == 200

    db.session.refresh(regular_user)
    assert regular_user.one_off_auth_token is None


def test_login_with_invalid_token(anon_user):
    """POST /auth/login with invalid token should return 404."""
    import uuid
    rv = anon_user.client.post(
        url_for("auth.LoginResource"),
        json={"token": str(uuid.uuid4())},
    )
    assert rv.status_code == 404


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------


def test_logout(regular_user):
    """GET /auth/logout should succeed for authenticated user."""
    rv = regular_user.client.get(url_for("auth.LogoutResource"))
    assert rv.status_code == 201
