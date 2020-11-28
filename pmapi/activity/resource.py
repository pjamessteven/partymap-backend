from flask import Blueprint, Response, request, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
import reverse_geocode
from sqlalchemy import or_, and_
from datetime import *
import time
import json
from geoalchemy2 import Geometry, func, Geography
from geoalchemy2.elements import WKTElement
from geoalchemy2.functions import ST_Distance_Sphere
from timezonefinder import TimezoneFinder

from pmapi.event_date.model import EventDate
from pmapi.extensions import db, activity_plugin
from pmapi.notification.controllers import create_notification

Activity = activity_plugin.activity_cls

activity_blueprint = Blueprint('activity', __name__)

@activity_blueprint.route('/<int:id>/revert/', methods=('GET',))
def revert(id):
    # THIS IS ALL FUCKED (well, only kinda. i'll deal with it later)
    # need to think about a good way to let users undo a recent change
    # without destroying everything
    activity = Activity.query.get(id)
    print('object:')
    print(activity.object.to_dict())
    print('object_version:')
    print(EventDate.to_dict(activity.object_version))
    print('after revert')
    object = activity.object_version.revert()
    print(EventDate.to_dict(activity.object_version))
    print(activity.object.versions)
    db.session.flush()
    new_activity = Activity(verb=u'revert', object=object) #might need to add event as target if eventdate etc.
    db.session.add(new_activity)
    db.session.commit()

    return jsonify({'ok': True}), 201
