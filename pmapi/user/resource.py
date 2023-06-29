from flask import Blueprint, jsonify

from flask_apispec import doc
from flask_apispec import marshal_with
from flask_apispec import MethodResource
from flask_apispec import use_kwargs
from flask_login import login_required
from marshmallow import fields
from marshmallow.validate import OneOf

from pmapi.utils import ROLES
from pmapi.common.controllers import paginated_view_args
from pmapi.exceptions import InvalidUsage
import pmapi.activity.controllers as activities
import pmapi.user.controllers as users

from .schemas import UserSchema, PrivateUserSchema, UserListSchema
from . import permissions as user_permissions

users_blueprint = Blueprint("users", __name__)


"""
@users_blueprint.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response
"""


@doc(tags=["users"])
class UsersResource(MethodResource):
    @doc(
        summary="Get a list of users that are in the db.",
        description="""Returns a list of users that are in the db. \n""",
    )
    @use_kwargs(
        {
            "query": fields.Str(description="search by username, email or UUID"),
            "status": fields.Str(
                description="Filter by status (staff+ only) (default: active)",
                missing="active",
                validate=OneOf(["active", "pending", "disabled", "all"]),
            ),
            "role": fields.Int(
                description="Show users by role (staff+ only)",
                validate=OneOf([*ROLES.values()]),
            ),
            **paginated_view_args(sort_options=["username", "created_at"]),
        },
        location="query"
    )
    @marshal_with(UserListSchema(), code=200)
    @user_permissions.get_users
    def get(self, **kwargs):
        return users.get_users(**kwargs)

    @doc(summary="Add a User", description="Adds a User")
    @use_kwargs(
        {
            "username": fields.Str(required=True),
            "email": fields.Email(required=True),
            # "activate": fields.Boolean(default=False),
            "password": fields.Str(default=None),
            "token": fields.Str(default=None),
        }
    )
    @marshal_with(PrivateUserSchema(), code=200)
    def post(self, **kwargs):
        return users.create_user(**kwargs)


users_blueprint.add_url_rule(
    "/", view_func=UsersResource.as_view("UsersResource"))


@doc(tags=["users"])
class UserResource(MethodResource):
    @doc(summary="Edit a User", description="Edits a User")
    @use_kwargs(
        {
            "username": fields.Str(required=False),
            "alias": fields.Str(required=False),
            "description": fields.Str(required=False),
            "email": fields.Email(required=False),
            "password": fields.Str(required=False),
            "password_confirm": fields.Str(required=False),
            "role": fields.Int(required=False),
            "status": fields.Str(required=False),
            "avatar": fields.Dict(required=False, allow_none=True)
        }
    )
    @marshal_with(PrivateUserSchema(), code=200)
    @login_required
    @user_permissions.update_user
    def put(self, user_id, **kwargs):
        return users.edit_user(user_id, **kwargs)

    @login_required
    @user_permissions.delete_user
    @doc(summary="Delete a User", description="Deletes a User")
    def delete(self, user_id):
        return users.delete_user(user_id)

    @marshal_with(UserSchema(), code=200)
    @doc(summary="Get a User", description="Gets a User")
    def get(self, user_id):
        return users.get_user_or_404(user_id)


users_blueprint.add_url_rule(
    "/<user_id>", view_func=UserResource.as_view("UserResource")
)


@doc(tags=["users"])
class PrivateUserResource(MethodResource):
    @user_permissions.get_user_full_profile
    @marshal_with(PrivateUserSchema(), code=200)
    @doc(summary="Get users full profile", description="Gets a User")
    def get(self, user_id):
        return users.get_user_or_404(user_id)


users_blueprint.add_url_rule(
    "/<user_id>/profile", view_func=PrivateUserResource.as_view("PrivateUserResource")
)


@doc(tags=["auth"])
class RequestPasswordResetResource(MethodResource):
    @doc(
        summary="Request password reset.",
    )
    def get(self, user_id):
        users.request_password_reset(user_id)
        return "", 200


users_blueprint.add_url_rule(
    "/<string:user_id>/request_pw_reset",
    view_func=RequestPasswordResetResource.as_view(
        "RequestPasswordResetResource"),
)


@doc(tags=["auth"])
class ResetPasswordResource(MethodResource):
    @doc(
        summary="Reset password",
    )
    @use_kwargs(
        {
            "password": fields.String(required=True),
            "password_confirm": fields.String(required=True),
        },
    )
    @marshal_with(PrivateUserSchema(), code=200)
    def post(self, token, **kwargs):
        return users.reset_password(token, **kwargs)


users_blueprint.add_url_rule(
    "/reset_pw/<string:token>",
    view_func=ResetPasswordResource.as_view("ResetPasswordResource"),
)


@doc(tags=["auth"])
class ActivateUserResource(MethodResource):
    @doc(
        summary="Activate user",
    )
    @marshal_with(PrivateUserSchema(), code=200)
    def post(self, token):
        return users.activate_user(token)


users_blueprint.add_url_rule(
    "/activate/<string:token>",
    view_func=ActivateUserResource.as_view("ActivateUserResource"),
)


@doc(tags=["auth"])
class ConfirmEmailResource(MethodResource):
    @doc(
        summary="Confirm email address when user updates their email address",
    )
    @marshal_with(PrivateUserSchema(), code=200)
    def post(self, token):
        return users.confirm_update_email(token)


users_blueprint.add_url_rule(
    "/confirm_email/<string:token>",
    view_func=ConfirmEmailResource.as_view("ConfirmEmailResource"),
)


@users_blueprint.route("/<string:username>/activity", methods=("GET",))
def user_activities(username):
    user = users.get_user_or_404(username)
    return jsonify(activities.get_activities_for_actor(user))
