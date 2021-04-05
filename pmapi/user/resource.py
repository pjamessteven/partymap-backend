from flask import Blueprint, Response, request, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required

from pmapi.event.model import *
from pmapi.user.model import User
from pmapi.exceptions import InvalidUsage
import pmapi.activity.controllers as activities
import pmapi.user.controllers as users
users_blueprint = Blueprint('users', __name__)


@users_blueprint.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

# update user
@users_blueprint.route('/', methods=('PUT', 'POST'))
def user():
    if request.method == 'PUT':
        user = User.query.get(current_user.id)
        data = request.get_json()
        print(data)
        if user:
            # if 'email' in data:
            # user.email = data['email']
            if 'username' in data:
                if db.session.query(User).filter(User.username == data['username']).count():
                    raise InvalidUsage(
                        message='username_already_registered', status_code=400)
                else:
                    user.username = data['username']
                    db.session.commit()
                    return jsonify(user=current_user.to_dict(), authenticated=True), 201
        else:
            raise InvalidUsage(message='Not authorized', status_code=401)
    elif request.method == 'POST':
        data = request.get_json()
        print(data)
        user = users.create_user(**data)
        return jsonify(user.to_dict()), 201

    else:
        raise InvalidUsage(message='Method not allowed', status_code=405)


@users_blueprint.route('/<string:id>', methods=('GET',))
def user_profile():
    pass

@users_blueprint.route('/activate/<string:token>', methods=('POST',))
def activate(token):
    activated_user = users.activate_user(token)
    return jsonify(activated_user.to_dict()), 200

@users_blueprint.route('/<string:username>/activity', methods=('GET',))
def user_activities(username):
    user = users.get_user_or_404(username)
    return jsonify(activities.get_activities_for_actor(user))
