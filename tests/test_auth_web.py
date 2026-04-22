import pytest
from flask import url_for


# ---------------------------------------------------------------------------
# Login / Logout
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="TODO")
def test_login_with_valid_credentials(regular_user):
    """POST /auth/login/ with valid email+password should return user object."""
    pass


@pytest.mark.skip(reason="TODO")
def test_login_with_invalid_credentials(anon_user):
    """POST /auth/login/ with bad password should return 401."""
    pass


@pytest.mark.skip(reason="TODO")
def test_login_with_token(anon_user, db):
    """POST /auth/login/ with a valid activation token should log the user in."""
    pass


@pytest.mark.skip(reason="TODO")
def test_logout(regular_user):
    """GET /auth/logout/ should log the user out."""
    pass


@pytest.mark.skip(reason="TODO")
def test_get_current_user_when_authenticated(regular_user):
    """GET /auth/login/ when authenticated should return current user."""
    pass


@pytest.mark.skip(reason="TODO")
def test_get_current_user_when_anon(anon_user):
    """GET /auth/login/ when anonymous should raise NotAuthenticated."""
    pass


# ---------------------------------------------------------------------------
# Apple sign-in
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="TODO")
def test_apple_login(mock_apple_auth, anon_user):
    """POST /auth/login/apple/ with a valid id_token should create or login user."""
    pass


@pytest.mark.skip(reason="TODO")
def test_apple_login_missing_token(anon_user):
    """POST /auth/login/apple/ without id_token should return 400."""
    pass


# ---------------------------------------------------------------------------
# Password reset & email confirmation
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="TODO")
def test_request_password_reset(anon_user, db):
    """GET /user/<id>/request_pw_reset should trigger a password reset email."""
    pass


@pytest.mark.skip(reason="TODO")
def test_reset_password_with_token(anon_user, db):
    """POST /user/reset_pw/<token> with valid token should reset password."""
    pass


@pytest.mark.skip(reason="TODO")
def test_activate_user_with_token(anon_user, db):
    """POST /user/activate/<token> should activate a pending user."""
    pass


@pytest.mark.skip(reason="TODO")
def test_confirm_email_with_token(anon_user, db):
    """POST /user/confirm_email/<token> should confirm the new email address."""
    pass
