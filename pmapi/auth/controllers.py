from werkzeug.security import check_password_hash
from flask_login import (
    login_user,
)
from flask import flash, session
import pmapi.exceptions as exc
from sqlalchemy.orm.exc import NoResultFound
import pmapi.user.controllers as users
from pmapi.extensions import db
from siwa import IdentityToken, KeyCache
from pmapi.user.model import User, OAuth
from flask import request


def authenticate_apple_user(id_token):

    # siwa library validates the JWT against Apple's public key

    # The cache is optional but will reduce the time taken
    # to validate tokens using the same public key

    cache = KeyCache()
    token = IdentityToken.parse(data=id_token)
    token_is_valid = token.is_validly_signed(
        key_cache=cache, audience='com.partymap.quasar')

    if not token_is_valid:
        # might be web user, try again with web client_id/audience
        token_is_valid = token.is_validly_signed(
            key_cache=cache, audience='com.partymap.web')

    if not token_is_valid:
        raise exc.InvalidAPIRequest("Token is invalid")

    email = token.payload.email
    user_id = token.payload.unique_apple_user_id

    token_json = {
        "email": email,
        "user_id": user_id,
        "email_is_private": token.payload.email_is_private,
        "expires_utc_seconds_since_epoch": token.payload.expires_utc_seconds_since_epoch,
        "issued_utc_seconds_since_epoch": token.payload.issued_utc_seconds_since_epoch
    }

    # Find this OAuth token in the database, or create it
    query = OAuth.query.filter_by(
        provider="apple", provider_user_id=user_id)
    try:
        oauth = query.one()
    except NoResultFound:
        oauth = OAuth(provider="apple",
                      provider_user_id=user_id, token=token_json)

    user = None

    if oauth.user:
        # apple user has authenticated with oauth before
        login_user(oauth.user)
        flash("Successfully signed in.")
        print("Signed in as:")
        print(oauth.user)
        user = oauth.user
    else:
        # first time logging in
        # with apple sign in, email is only returned the first time
        existing_user = users.get_user_by_email(email)
        if (existing_user == None):
            # Create a new local user account for this user
            user = User(email=email)
            db.session.add(user)
            db.session.flush()
        else:
            user = existing_user
        user.oauth = True
        # Associate the new local user account with the OAuth token
        oauth.user_id = user.id
        # activate account
        user.activate()

        # Log in the new account
        login_user(user)
        flash("Successfully signed in.")

        # Save and commit our database models
        db.session.add_all([user, oauth])
        db.session.commit()

    # have to do a custom redirect flow for android  capacitor app
    if request.args.get("android_capacitor"):
        user.one_off_auth_token = str(uuid.uuid4())
        next_url = "https://partymap.com" + '?token=' + user.one_off_auth_token
        db.session.commit()
        return redirect('/oauth_redirect?redirect_uri='+next_url)

    return user


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
        user = users.get_user_by_token_or_404(one_off_token)
        if user:
            # delete one off token
            user.one_off_auth_token = None
            db.session.add(user)
            db.session.commit()
            # flask-login
            login_user(user, remember=remember)
            session.permanent = True
            return user
    elif not identifier or not password:
        raise exc.LoginRequired()
    else:
        user = users.get_user_or_404(identifier)

    if not user:
        raise exc.LoginRequired()

    # don't allow pending or disabled accounts to login
    if user.status == "disabled":
        raise exc.UserDisabled()
    elif user.status == "pending":
        raise exc.UserPending()

    if not check_password_hash(user.password, password):
        session["attempt"] = session["attempt"] - 1
        raise exc.InvalidAPIRequest(
            "Login failed, try again..."
        )

    # flask-login
    login_user(user, remember=remember)
    session.permanent = True
    return user
