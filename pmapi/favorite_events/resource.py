from flask import Blueprint, Response, request, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from timezonefinder import TimezoneFinder
import reverse_geocode
import pygeohash as pgh
from dateutil.rrule import *
from datetime import *
from dateutil.relativedelta import *
from pytz import timezone, utc
from pytz.exceptions import UnknownTimeZoneError

from pmapi.user.model import User
from pmapi.event.model import *
from pmapi.exceptions import InvalidUsage
from pmapi.event_tag.model import *

favorites_blueprint = Blueprint('favorites', __name__)

per_page = 20

@favorites_blueprint.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

#get users favorite events
@favorites_blueprint.route('/', methods=('GET',))
@login_required
def fetch_favorites():
    # TO DO
    # ENABLE PAGINATION BY DOING A PROPER QUERY ON THE ASSOICIATION TABLE
    # QUERY MIN AND MAX DATE TOO
    if not current_user.is_authenticated:
        return jsonify({ 'message': 'Not authenticated', }), 401
    favorites = Event.query.join(favorites_association_table).join(EventDate).filter((favorites_association_table.c.user == current_user.id))
    favorites = favorites.order_by(EventDate.event_start).all()
    return jsonify ([e.next_event().minified() for e in favorites]), 201

#toggle whether or not this event is faved by current user
@favorites_blueprint.route('/<int:id>', methods=('PUT',))
@login_required
def toggle_favorite(id):
    event = Event.query.get(int(id))

    fav_state = event.favorite(user_id=current_user.id)
    print(event)
    print(fav_state)
    return jsonify(fav_status=fav_state)
