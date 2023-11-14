from flask import flash, current_app
from flask_login import current_user, login_user
from flask_dance.contrib.facebook import make_facebook_blueprint
from flask_dance.consumer import oauth_authorized, oauth_error, oauth_before_login
from flask_dance.consumer.storage.sqla import SQLAlchemyStorage
from sqlalchemy.orm.exc import NoResultFound
from flask import request, session, redirect

from pmapi.user.model import User, OAuth
from pmapi.extensions import db, cache

import pmapi.user.controllers as users

oauth_fb_blueprint = make_facebook_blueprint(
    storage=SQLAlchemyStorage(
        OAuth, db.session, cache=cache, user=current_user),
    scope="email,public_profile",
)

# OAUTH HAS BEEN DISABLED IN application.py


@oauth_before_login.connect_via(oauth_fb_blueprint)
def before_login(blueprint, url):
    session["next_url"] = request.args.get("next_url")
    session["mobile"] = request.args.get("mobile")


# create/login local user on successful OAuth login
@oauth_authorized.connect_via(oauth_fb_blueprint)
def facebook_logged_in(blueprint, token):
    if not token:
        flash("Failed to log in.", category="error")
        return False

    resp = blueprint.session.get("me?fields=id,name,email")
    if not resp.ok:
        msg = "Failed to fetch user info."
        flash(msg, category="error")
        return False

    info = resp.json()

    # Set base_url
    if current_app.config["DEBUG"] is True:
        base_url = "http://localhost:9000"
    else:
        base_url = "https://partymap.com"

    # append next path
    if session["next_url"]:
        next_url = base_url + session["next_url"]
    else:
        next_url = base_url

    user_id = info["id"]

    # Find this OAuth token in the database, or create it
    query = OAuth.query.filter_by(
        provider=blueprint.name, provider_user_id=user_id)
    try:
        oauth = query.one()
    except NoResultFound:
        oauth = OAuth(provider=blueprint.name,
                      provider_user_id=user_id, token=token)

    user = None

    if oauth.user:
        login_user(oauth.user)
        flash("Successfully signed in.")
        print("Signed in as:")
        print(oauth.user)
    else:
        existingUser = users.get_user_by_email(info["email"])
        if (existingUser == None):
            # Create a new local user account for this user
            user = User(email=info["email"])
        else:
            user = existingUser
        user.oauth = True
        # Associate the new local user account with the OAuth token
        oauth.user = user
        # activate account
        user.activate()

    # for native mobile auth we pass a token that is used to authenticate with /login
    if session["mobile"]:
        user.one_off_auth_token = str(uuid.uuid4())
        next_url = next_url + '?token=' + user.one_off_auth_token

    else:
        # Log in the new local user account
        login_user(user)
        flash("Successfully signed in.")

    # Save and commit our database models
    db.session.add_all([user, oauth])
    db.session.commit()

    if session["mobile"]:
        return redirect('/oauth_redirect?redirect_uri='+next_url)
    else:
        return redirect(next_url)

    #    return redirect(next_url)

    # Disable Flask-Dance's default behavior for saving the OAuth token
    # return False


# notify on OAuth provider error
@oauth_error.connect_via(oauth_fb_blueprint)
def facebook_error(blueprint, message, response):
    msg = ("OAuth error from {name}! " "message={message} response={response}").format(
        name=blueprint.name, message=message, response=response
    )
    flash(msg, category="error")
