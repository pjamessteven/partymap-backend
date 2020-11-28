"""
config.py
- settings for the flask application object
"""
import os

class BaseConfig(object):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///partymap.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # used for encryption and session management
    SECRET_KEY = 'u*+FF@b<a?upsABSuI]%v5sYu$c3Tc'
    # Uploads
    TOP_LEVEL_DIR = os.path.abspath(os.curdir)

    ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
    IMAGE_UPLOAD_FOLDER = TOP_LEVEL_DIR + '/static/img/'
    THUMB_UPLOAD_FOLDER = TOP_LEVEL_DIR + '/static/thumbs/'

    UPLOADS_URL = 'http://localhost:5000/static/img/'

    OAUTH_CREDENTIALS = {
    'facebook': {
    'id': '662775247475653',
    'secret': '0c61582466a0d3124e73d9f60ba3d05d'
    }
    }
