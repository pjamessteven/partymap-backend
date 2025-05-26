from datetime import datetime
from pmapi.media_item.schemas import generate_filepath, generate_local_filepath
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import event
import os
import uuid
from pmapi.extensions import db
import logging


class FlaskUsage(db.Model):
    __tablename__ = 'flask_usage' # Explicitly tells SQLAlchemy the table name

    # Define db.Columns based on your CREATE TABLE statement
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(512))
    ua_browser = db.Column(db.String(16))
    ua_language = db.Column(db.String(16))
    ua_platform = db.Column(db.String(16))
    ua_version = db.Column(db.String(16))
    blueprint = db.Column(db.String(64))
    view_args = db.Column(db.String(64)) # Use String for VARCHAR, even if it's JSON-like
    status = db.Column(db.Integer)
    remote_addr = db.Column(db.String(24))
    xforwardedfor = db.Column(db.String(24))
    authorization = db.Column(db.Boolean)
    ip_info = db.Column(db.String(2048)) # Use String for VARCHAR, even if it's JSON-like
    path = db.Column(db.String(128))
    speed = db.Column(db.Float) # double precision maps to Float
    datetime = db.Column(db.DateTime) # timestamp without time zone maps to DateTime
    username = db.Column(db.String(128))
    track_var = db.Column(db.String(128))