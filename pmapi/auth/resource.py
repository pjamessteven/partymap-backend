from flask import Blueprint, Response, request, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
import time

import pmapi.exceptions as exc
from pmapi.user.model import User
from pmapi.extensions import db, lm, cache

auth_blueprint = Blueprint('auth', __name__)


@lm.user_loader
def load_user(user_id):
    print('load_user called')
    print(user_id)
    try:
        return User.query.get(user_id)
    except:
        return None


@auth_blueprint.route('/login/', methods=('POST', 'GET'))
def login():
    if request.method == 'POST':
        data = request.get_json()
        print(data)
        user = User.authenticate(**data)

        # don't allow pending or disabled accounts to login
        if user.status == "disabled":
            raise exc.UserDisabled()
        elif user.status == "pending":
            raise exc.UserPending()

        # flask-login
        login_user(user, remember=True)

        # am I vulnerable to open redirects?
        return jsonify(user=user.to_dict(), authenticated=True), 201

    if request.method == 'GET':
        if current_user.is_authenticated:
            return jsonify(user=current_user.to_dict(), authenticated=True), 201

        else:
            return jsonify(message='No login token', authenticated=False), 401


@auth_blueprint.route('/logout/', methods=('GET',))
def logout():
    logout_user()
    return ('', 201)
