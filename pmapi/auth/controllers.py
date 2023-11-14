from werkzeug.security import check_password_hash
from flask_login import (
    login_user,
)
from flask import session
import pmapi.exceptions as exc
import pmapi.user.controllers as users


def authenticate_user(**kwargs):
    identifier = kwargs.get("identifier")
    password = kwargs.get("password")
    remember = kwargs.get("remember", False)
    one_off_token = kwargs.get("token", None)

    if session["attempt"] == 0:
        raise exc.InvalidAPIRequest(
            "Too many login attempts. Try again later or reset your password"
        )

    if one_off_token is not None:
        user = users.get_user_by_token_or_404(identifier)
        if user:
            # delete one off token
            user.one_off_auth_token = None
            db.session.add(user)
            db.session.commit()
    elif not identifier or not password:
        raise exc.LoginRequired()
    else:
        user = users.get_user_or_404(identifier)

    # don't allow pending or disabled accounts to login
    if user.status == "disabled":
        raise exc.UserDisabled()
    elif user.status == "pending":
        raise exc.UserPending()

    if not user:
        raise exc.LoginRequired()

    if not check_password_hash(user.password, password):
        session["attempt"] = session["attempt"] - 1
        raise exc.InvalidAPIRequest(
            "Login failed, try again..."
        )
    # flask-login
    login_user(user, remember=remember)

    session.permanent = True

    return user
