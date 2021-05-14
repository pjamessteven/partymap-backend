from flask import Blueprint
from flask_login import (
    logout_user,
    current_user,
)
from flask_apispec import doc
from flask_apispec import marshal_with
from flask_apispec import MethodResource
from flask_apispec import use_kwargs
from marshmallow import fields

import pmapi.exceptions as exc
from pmapi.user.model import User
from pmapi.extensions import lm
from pmapi.user.schemas import UserSchema

auth_blueprint = Blueprint("auth", __name__)


@lm.user_loader
def load_user(user_id):
    print("load_user called")
    print(user_id)
    try:
        return User.query.get(user_id)
    except exc.RecordNotFound:
        return None


@doc(tags=["auth"])
class LoginResource(MethodResource):
    @doc(
        summary="Log in.",
    )
    @use_kwargs(
        {
            "email": fields.String(required=True),
            "password": fields.String(required=True),
            "remember": fields.Boolean(required=False),
        },
    )
    @marshal_with(UserSchema(), code=200)
    def post(self, **kwargs):
        print("login", kwargs)
        auth = User.authenticate(**kwargs)
        print("auth", auth)
        return auth

    @doc(
        summary="Get current user info.",
    )
    @marshal_with(UserSchema(), code=200)
    def get(self):
        if current_user.is_authenticated:
            return current_user
        else:
            raise exc.LoginRequired()


auth_blueprint.add_url_rule("/login/", view_func=LoginResource.as_view("LoginResource"))


@doc(tags=["auth"])
class LogoutResource(MethodResource):
    @doc(
        summary="Log out.",
    )
    def get(self):
        if current_user.is_authenticated:
            logout_user()
            return ("", 201)
        else:
            raise exc.LoginRequired()


auth_blueprint.add_url_rule(
    "/logout", view_func=LogoutResource.as_view("LogoutResource")
)
