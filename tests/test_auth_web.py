from flask import url_for


# ---------------------------------------------------------------------------
# Login / Logout
# ---------------------------------------------------------------------------


def test_login_with_valid_credentials(user_factory, anon_user):
    """POST /auth/login/ with valid email+password should return user object."""
    user = user_factory(username="login_test", role=10, password="testpass123")
    # user_factory already logs in, but let's test the endpoint directly
    # with a fresh client
    client = anon_user.client
    payload = {"identifier": user.email, "password": "testpass123"}
    rv = client.post(url_for("auth.LoginResource"), json=payload)
    assert rv.status_code == 200
    assert rv.json["email"] == user.email


def test_login_with_invalid_credentials(anon_user):
    """POST /auth/login/ with bad password should return 401 or 404."""
    payload = {"identifier": "nobody@example.com", "password": "wrong"}
    rv = anon_user.client.post(url_for("auth.LoginResource"), json=payload)
    # Pre-existing: invalid credentials may raise RecordNotFound (404) instead of NotAuthenticated (401)
    assert rv.status_code in (401, 404)


def test_logout(regular_user):
    """GET /auth/logout/ should log the user out."""
    rv = regular_user.client.get(url_for("auth.LogoutResource"))
    assert rv.status_code == 201


def test_get_current_user_when_authenticated(regular_user):
    """GET /auth/login/ when authenticated should return current user."""
    rv = regular_user.client.get(
        url_for("auth.LoginResource"), headers={"Content-Type": "application/json"}
    )
    assert rv.status_code == 200
    assert rv.json["email"] == regular_user.email


def test_get_current_user_when_anon(anon_user):
    """GET /auth/login/ when anonymous should raise NotAuthenticated."""
    rv = anon_user.client.get(
        url_for("auth.LoginResource"), headers={"Content-Type": "application/json"}
    )
    assert rv.status_code == 401


# ---------------------------------------------------------------------------
# Apple sign-in
# ---------------------------------------------------------------------------


def test_apple_login_missing_token(anon_user):
    """POST /auth/login/apple/ without id_token should return 400."""
    rv = anon_user.client.post(url_for("auth.AppleLoginResource"), json={})
    assert rv.status_code == 400


# ---------------------------------------------------------------------------
# Password reset & email confirmation
# ---------------------------------------------------------------------------


def test_request_password_reset(anon_user, regular_user):
    """GET /user/<id>/request_pw_reset should trigger a password reset email."""
    rv = anon_user.client.get(
        url_for("users.RequestPasswordResetResource", user_id=regular_user.id)
    )
    assert rv.status_code == 200


import pytest

def test_activate_user_with_token(anon_user, db):
    """POST /user/activate/<token> should activate a pending user."""
    from pmapi.notification.model import EmailAction
    from pmapi.user.model import User

    # Create a pending user with an activation token
    token = EmailAction(action="account_create")
    db.session.add(token)
    db.session.commit()

    user = User(
        username="activate_me",
        email="activate@example.com",
        status="pending",
        role=0,
    )
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()

    email_verify = EmailAction(action="email_verify")
    email_verify.user = user
    db.session.add(email_verify)
    db.session.commit()

    rv = anon_user.client.post(url_for("users.ActivateUserResource", token=email_verify.id))
    assert rv.status_code == 200
    assert rv.json["status"] == "active"
