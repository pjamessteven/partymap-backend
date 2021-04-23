from flask import Blueprint, jsonify

from flask_apispec import doc
from flask_apispec import marshal_with
from flask_apispec import MethodResource
from flask_apispec import use_kwargs
from marshmallow import fields
from marshmallow.validate import OneOf

from pmapi.utils import ROLES
from pmapi.common.controllers import paginated_view_args
from pmapi.exceptions import InvalidUsage
import pmapi.activity.controllers as activities
import pmapi.user.controllers as users

from .schemas import UserSchema

users_blueprint = Blueprint("users", __name__)


@users_blueprint.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@doc(tags=["users"])
class UsersResource(MethodResource):
    list_users_args = {
        "username": fields.Str(description="search by username"),
        "status": fields.Str(
            description="Filter by status (staff+ only) (default: active)",
            missing="active",
            validate=OneOf(["active", "pending", "disabled", "all"]),
        ),
        "role": fields.Int(
            description="Show users by role (staff+ only)",
            validate=OneOf([*ROLES.values()]),
        ),
        **paginated_view_args(sort_options=["username", "created", "modified"]),
    }

    @doc(summary="Add a User", description="Adds a User")
    @use_kwargs(
        {
            "username": fields.Str(required=True),
            "email": fields.Email(required=True),
            "activate": fields.Boolean(default=False),
            "password": fields.Str(default=None),
            "token": fields.Str(default=None),
        }
    )
    @marshal_with(UserSchema(), code=200)
    def post(self, **kwargs):
        return users.create_user_with_token(**kwargs)


users_blueprint.add_url_rule("/", view_func=UsersResource.as_view("UsersResource"))

"""
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
                if db.session.query(User).filter(User.username ==
                data['username']).count():
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
"""


@users_blueprint.route("/<string:id>", methods=("GET",))
def user_profile():
    pass


@users_blueprint.route("/activate/<string:token>", methods=("POST",))
def activate(token):
    activated_user = users.activate_user(token)
    return jsonify(activated_user.to_dict()), 200


@users_blueprint.route("/<string:username>/activity", methods=("GET",))
def user_activities(username):
    user = users.get_user_or_404(username)
    return jsonify(activities.get_activities_for_actor(user))
