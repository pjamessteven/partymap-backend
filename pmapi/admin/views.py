from flask import Flask, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user, login_required
from flask_admin import Admin, AdminIndexView, BaseView
from flask_admin.contrib.sqla import ModelView
from flask import redirect, url_for, request
from flask_login import logout_user, current_user
from flask_admin import BaseView, expose

# Custom admin view that requires login
class SecureModelView(ModelView):
    def is_accessible(self):
        # Check if user is authenticated and active
        return current_user.is_authenticated and current_user.is_active and current_user.role > 20

    def inaccessible_callback(self, name, **kwargs):
        # Redirect to login page if not authenticated
        return redirect(url_for('login', next=request.url))

# Custom admin index view that requires login
class SecureAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_active

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login', next=request.url))



class LogoutMenuLink(BaseView):
    def is_accessible(self):
        return current_user.is_authenticated

    def get_menu_link(self):
        # Customize the menu link to show username
        if current_user.is_authenticated:
            return f'Logout ({current_user.username})'
        return 'Logout'

    @expose('/')
    def index(self):
        # Log out the user
        logout_user()
        
        # Optional: Add a flash message
        flash('You have been logged out.', 'success')
        
        # Redirect to login page, preserving any 'next' parameter if exists
        next_url = request.args.get('next') or url_for('auth.LoginResource')
        return redirect(next_url)
    
class UserModelView(SecureModelView):
    column_searchable_list = ['username', 'email', 'alias', 'description']
    column_exclude_list = ['password', ]

class EventModelView(SecureModelView):
    column_searchable_list = ['name', 'creator_id', 'id', 'host_id', 'description', 'full_description']
    column_filters = ['created_at']

class EventDateModelView(SecureModelView):
    column_searchable_list = ['event_id', 'description']
    #column_filters = ['country']
    column_filters = ['start_naive', 'end_naive', 'created_at']

class EventLocationModelView(SecureModelView):
    column_searchable_list = ['name', 'description']
    column_filters = ['country', 'country_id', 'region', 'locality']

class EventArtistModelView(SecureModelView):
    column_searchable_list = ['name', 'mbid', 'description', 'disambiguation']
    column_filters = ['country']