from pmapi.user.model import User
from pmapi.extensions import db, lm, cache
from flask import Blueprint, Response, request, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
import time
auth_blueprint = Blueprint('auth', __name__)


@lm.user_loader
def load_user(user_id):
    print('load_user called')
    print(user_id)
    start_time = time.time()
    user = User.query.get(user_id)
    print('user loaded')
    print('elapsed: ' + str(time.time() - start_time))
    return user


@auth_blueprint.route('/login/', methods=('POST', 'GET'))
def login():
    if request.method == 'POST':
        data = request.get_json()
        print(data)
        user = User.authenticate(**data)
        print(user)
        if not user:
            return jsonify(message='Invalid credentials', authenticated=False), 401

        # flask-login
        login_user(user, remember=True)
        print(current_user)

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
