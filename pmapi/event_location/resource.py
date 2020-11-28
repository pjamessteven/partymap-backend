from flask import Blueprint, Response, request, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from sqlalchemy import or_, and_
import datetime
import time

from pmapi.event.model import *
from pmapi.event_artist.model import *
from pmapi.event_tag.model import *
from pmapi.event_date.model import *

from .model import EventLocation

locations_blueprint = Blueprint('locations', __name__)

# get all locations
@locations_blueprint.route('/', methods=('GET',))
def fetch_points():
    if request.args.get('min'):
        min = datetime.utcfromtimestamp(int(request.args.get('min'))/1000)
    else: min = datetime.utcfromtimestamp(time.time())
    if request.args.get('max') == 'Infinity':
        max = datetime.utcfromtimestamp(time.time()+(86400*730)) #two years from now
    elif request.args.get('max'):
        max = datetime.utcfromtimestamp(int(request.args.get('max'))/1000)
    else: max = datetime.utcfromtimestamp(time.time()+(86400*730)) #two years from now

    if request.args.get('tags[]'):
        tags = request.args.getlist('tags[]')
        print(tags)
        event_locations = db.session.query(
                EventLocation
                ).join(
                    EventDate
                ).join(
                    Event)

        for tag in tags:
            event_locations = event_locations.filter(
                                and_(
                                    or_(EventDate.artists.any(EventArtist.artist_name==tag),
                                        Event.event_tags.any(EventTag.tag_id==tag)),
                                    or_(
                                        and_(EventDate.event_start_naive>=min,and_(EventDate.event_end_naive<=max, EventDate.event_end_naive>=min)),
                                        and_(EventDate.event_start_naive>=min,EventDate.event_start_naive<=max),
                                        )
                                )
                            )

    else:
        print('here')
        event_locations = db.session.query(
                                EventLocation
                            ).join(
                                EventDate
                            ).filter(
                                or_(
                                    and_(EventDate.event_start_naive>=min,and_(EventDate.event_end_naive<=max, EventDate.event_end_naive>=min)),
                                    and_(EventDate.event_start_naive>=min,EventDate.event_start_naive<=max),
                                    )
                                ).all()

    print(min)
    print(max)
    print(event_locations)

    return jsonify ([e.to_point_dict() for e in event_locations]), 201
