from flask import url_for
import pytest


# ---------------------------------------------------------------------------
# Get users
# ---------------------------------------------------------------------------


def test_get_users_list(anon_user):
    """GET /user/ should return paginated list of active users."""
    rv = anon_user.client.get(url_for("users.UsersResource"))
    assert rv.status_code == 200
    assert "items" in rv.json


def test_get_users_by_query(anon_user, regular_user):
    """GET /user/?query=... should search users."""
    rv = anon_user.client.get(
        url_for("users.UsersResource", query=regular_user.username)
    )
    assert rv.status_code == 200


def test_get_users_by_role_forbidden(anon_user):
    """GET /user/?role=... as anon should return 403."""
    rv = anon_user.client.get(url_for("users.UsersResource", role=10))
    assert rv.status_code == 403


def test_get_users_by_role_as_staff(staff_user):
    """GET /user/?role=... as staff should succeed."""
    rv = staff_user.client.get(url_for("users.UsersResource", role=10))
    assert rv.status_code == 200


def test_get_user_by_id(anon_user, regular_user):
    """GET /user/<id> should return user info."""
    rv = anon_user.client.get(url_for("users.UserResource", user_id=regular_user.id))
    assert rv.status_code == 200
    assert rv.json["username"] == regular_user.username


def test_get_user_not_found(anon_user):
    """GET /user/<nonexistent_id> should return 404."""
    rv = anon_user.client.get(url_for("users.UserResource", user_id="nonexistent"))
    assert rv.status_code == 404


# ---------------------------------------------------------------------------
# Edit user
# ---------------------------------------------------------------------------


def test_edit_user_username(regular_user, db):
    """PUT /user/<id> should update username."""
    rv = regular_user.client.put(
        url_for("users.UserResource", user_id=regular_user.id),
        json={"username": "new_username"},
    )
    assert rv.status_code == 200
    assert rv.json["username"] == "new_username"


def test_edit_user_alias(regular_user):
    """PUT /user/<id> should update alias."""
    rv = regular_user.client.put(
        url_for("users.UserResource", user_id=regular_user.id),
        json={"alias": "DJ Test"},
    )
    assert rv.status_code == 200
    assert rv.json["alias"] == "DJ Test"


def test_edit_user_description(regular_user):
    """PUT /user/<id> should update description."""
    rv = regular_user.client.put(
        url_for("users.UserResource", user_id=regular_user.id),
        json={"description": "I love parties"},
    )
    assert rv.status_code == 200
    assert rv.json["description"] == "I love parties"


def test_edit_user_password(regular_user, db):
    """PUT /user/<id> should update password."""
    rv = regular_user.client.put(
        url_for("users.UserResource", user_id=regular_user.id),
        json={"password": "new_password_123", "password_confirm": "new_password_123"},
    )
    assert rv.status_code == 200


def test_edit_user_password_mismatch(regular_user):
    """PUT /user/<id> with mismatched passwords should fail."""
    rv = regular_user.client.put(
        url_for("users.UserResource", user_id=regular_user.id),
        json={"password": "newpass", "password_confirm": "different"},
    )
    assert rv.status_code == 400


def test_edit_user_email_sends_verification(regular_user):
    """PUT /user/<id> email as non-staff should trigger verification email."""
    rv = regular_user.client.put(
        url_for("users.UserResource", user_id=regular_user.id),
        json={"email": "new_email@example.com"},
    )
    assert rv.status_code == 200


def test_edit_user_email_as_staff(staff_user, regular_user, db):
    """PUT /user/<id> email as staff should update immediately."""
    rv = staff_user.client.put(
        url_for("users.UserResource", user_id=regular_user.id),
        json={"email": "staff_updated@example.com"},
    )
    assert rv.status_code == 200
    assert rv.json["email"] == "staff_updated@example.com"


def test_edit_user_role_as_admin(admin_user, regular_user):
    """PUT /user/<id> role as admin should update role."""
    rv = admin_user.client.put(
        url_for("users.UserResource", user_id=regular_user.id),
        json={"role": 20},
    )
    assert rv.status_code == 200
    assert rv.json["role"] == 20


def test_edit_user_role_forbidden(regular_user, regular_user_factory):
    """PUT /user/<id> role as non-admin should fail."""
    other = regular_user_factory()
    rv = regular_user.client.put(
        url_for("users.UserResource", user_id=other.id),
        json={"role": 20},
    )
    assert rv.status_code == 403


def test_edit_other_user_forbidden(regular_user, regular_user_factory):
    """PUT /user/<id> for another user as non-staff should fail."""
    other = regular_user_factory()
    rv = regular_user.client.put(
        url_for("users.UserResource", user_id=other.id),
        json={"username": "hacked"},
    )
    assert rv.status_code == 403


# ---------------------------------------------------------------------------
# Delete user
# ---------------------------------------------------------------------------


def test_delete_user_self(regular_user):
    """DELETE /user/<id> as self should succeed."""
    rv = regular_user.client.delete(
        url_for("users.UserResource", user_id=regular_user.id)
    )
    assert rv.status_code == 201


def test_delete_user_as_staff(staff_user, regular_user_factory):
    """DELETE /user/<id> as staff should succeed."""
    other = regular_user_factory()
    rv = staff_user.client.delete(
        url_for("users.UserResource", user_id=other.id)
    )
    assert rv.status_code == 201


def test_delete_other_user_forbidden(regular_user, regular_user_factory):
    """DELETE /user/<id> for another user as non-staff should fail."""
    other = regular_user_factory()
    rv = regular_user.client.delete(
        url_for("users.UserResource", user_id=other.id)
    )
    assert rv.status_code == 403


# ---------------------------------------------------------------------------
# Password reset
# ---------------------------------------------------------------------------


def test_request_password_reset(anon_user, regular_user):
    """GET /user/<id>/request_pw_reset should succeed."""
    rv = anon_user.client.get(
        url_for("users.RequestPasswordResetResource", user_id=regular_user.id)
    )
    assert rv.status_code == 200


def test_request_password_reset_user_not_found(anon_user):
    """GET /user/<nonexistent>/request_pw_reset should return 404."""
    rv = anon_user.client.get(
        url_for("users.RequestPasswordResetResource", user_id="nobody")
    )
    assert rv.status_code == 404


def test_reset_password(anon_user, regular_user, db):
    """POST /user/reset_pw/<token> should reset password."""
    from pmapi.notification.model import EmailAction

    action = EmailAction(user=regular_user, action="password_reset")
    db.session.add(action)
    db.session.commit()

    rv = anon_user.client.post(
        url_for("users.ResetPasswordResource", token=action.id),
        json={"password": "new_password_123", "password_confirm": "new_password_123"},
    )
    assert rv.status_code == 200


def test_reset_password_mismatch(anon_user, regular_user, db):
    """POST /user/reset_pw/<token> with mismatched passwords should fail."""
    from pmapi.notification.model import EmailAction

    action = EmailAction(user=regular_user, action="password_reset")
    db.session.add(action)
    db.session.commit()

    rv = anon_user.client.post(
        url_for("users.ResetPasswordResource", token=action.id),
        json={"password": "newpass", "password_confirm": "different"},
    )
    assert rv.status_code == 400


def test_reset_password_invalid_token(anon_user):
    """POST /user/reset_pw/<bad_token> should return 404."""
    rv = anon_user.client.post(
        url_for("users.ResetPasswordResource", token="nonexistent"),
        json={"password": "newpass", "password_confirm": "newpass"},
    )
    assert rv.status_code == 404


# ---------------------------------------------------------------------------
# Confirm email
# ---------------------------------------------------------------------------


def test_confirm_email_update(anon_user, regular_user, db):
    """POST /user/confirm_email/<token> should update email."""
    from pmapi.notification.model import EmailAction

    action = EmailAction(
        user=regular_user, action="email_verify", extra_data="confirmed@example.com"
    )
    db.session.add(action)
    db.session.commit()

    rv = anon_user.client.post(
        url_for("users.ConfirmEmailResource", token=action.id)
    )
    assert rv.status_code == 200
    assert rv.json["email"] == "confirmed@example.com"


def test_confirm_email_invalid_token(anon_user):
    """POST /user/confirm_email/<bad_token> should return 404."""
    rv = anon_user.client.post(
        url_for("users.ConfirmEmailResource", token="nonexistent")
    )
    assert rv.status_code == 404


# ---------------------------------------------------------------------------
# Full profile (staff only)
# ---------------------------------------------------------------------------


def test_get_full_profile_as_staff(staff_user, regular_user):
    """GET /user/<id>/profile as staff should succeed."""
    rv = staff_user.client.get(
        url_for("users.PrivateUserResource", user_id=regular_user.id)
    )
    assert rv.status_code == 200


def test_get_full_profile_forbidden(regular_user, regular_user_factory):
    """GET /user/<id>/profile as non-staff should fail."""
    other = regular_user_factory()
    rv = regular_user.client.get(
        url_for("users.PrivateUserResource", user_id=other.id)
    )
    assert rv.status_code == 403
