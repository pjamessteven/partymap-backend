from flask import Blueprint, request, render_template, redirect, url_for, make_response
from flask_login import logout_user, current_user, AnonymousUserMixin
from flask_apispec import doc
from flask_apispec import marshal_with
from flask_apispec import MethodResource
from flask_apispec import use_kwargs
from marshmallow import fields
from pmapi.auth.controllers import authenticate_apple_user, authenticate_user
import pmapi.exceptions as exc

import pmapi.exceptions as exc
from pmapi.user.model import User
from pmapi.extensions import lm, db
from pmapi.user.schemas import PrivateUserSchema

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
            "identifier": fields.String(required=False),
            "password": fields.String(required=False),
            "remember": fields.Boolean(required=False),
            "token": fields.String(required=False),
        },
    )
    def post(self, **kwargs):
       # If it's a browser request
        if not request.is_json and request.method == 'POST':
            # Extract form data for browser login
            kwargs = {
                'identifier': request.form.get('identifier'),
                'password': request.form.get('password'),
                'remember': request.form.get('remember', False)
            }
        
        try:
            user = authenticate_user(**kwargs)
            
            # If it's a browser request, redirect
            if not request.is_json:
                next_url = request.args.get('next') or request.form.get('next') or url_for('admin.index')
                return redirect(next_url)
            else:
                return marshal_with(PrivateUserSchema(), code=200)(lambda: user)()     
        
        except exc.NotAuthenticated:
            # Handle authentication failure
            if not request.is_json:
                response = make_response(render_template('login.html', error='Invalid credentials'))
                response.headers['Content-Type'] = 'text/html'
                return response, 401
            raise

    @doc(
        summary="Get login page or current user info if already authenticated.",
    )
    def get(self):

        # Check if it's a browser request
        if not request.is_json:
            # If not authenticated, show login page
            if not current_user.is_authenticated:
                response = make_response(render_template('login.html'))
                response.headers['Content-Type'] = 'text/html'
                return response

            else:
                next_url = request.args.get('next') or url_for('admin.index')
                return redirect(next_url)        
                    
        if current_user.is_authenticated:
            return marshal_with(PrivateUserSchema(), code=200)(lambda: current_user)()

        else:
            raise exc.NotAuthenticated()
        

auth_blueprint.add_url_rule(
    "/login/", view_func=LoginResource.as_view("LoginResource"))


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
    "/logout/", view_func=LogoutResource.as_view("LogoutResource")
)


@doc(tags=["auth"])
class AppleLoginResource(MethodResource):
    @doc(
        summary="Validate Sign in with Apple token and login or create user",
    )
    @use_kwargs(
        {
            "id_token": fields.String(required=False),
        },
    )
    @marshal_with(PrivateUserSchema(), code=200)
    def post(self, **kwargs):
        id_token = kwargs.get("id_token")
        # if we're receiving a post request directly from apple
        # id_token will be in form
        if id_token is None:
            id_token = request.form.get('id_token')
        if id_token is None:
            raise exc.InvalidAPIRequest("Token is required")

        return authenticate_apple_user(id_token)


auth_blueprint.add_url_rule(
    "/login/apple/", view_func=AppleLoginResource.as_view("AppleLoginResource"))
