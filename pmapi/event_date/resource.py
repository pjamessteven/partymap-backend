from flask import Blueprint, Response, request, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
import reverse_geocode
import pygeohash as pgh
from sqlalchemy import or_, and_
from datetime import *
import time
import json
from geoalchemy2 import Geometry, func, Geography
from geoalchemy2.elements import WKTElement
from geoalchemy2.functions import ST_Distance_Sphere
from timezonefinder import TimezoneFinder
from pytz import timezone, utc
from pytz.exceptions import UnknownTimeZoneError

from pmapi.event.model import Event
from pmapi.notification.controllers import create_notification
from pmapi.extensions import db, activity_plugin
from pmapi.event_location.model import EventLocation, EventLocationType
from .model import EventDate


per_page = 20

event_dates_blueprint = Blueprint('event_dates', __name__)

Activity = activity_plugin.activity_cls


# get all event_date for an event
@event_dates_blueprint.route('/event/<int:id>/', methods=('GET',))
def eventdates(id):
    eventdate = Event.query.get(id).event_dates

    if current_user.is_authenticated:
        # return is favorited
        return jsonify({'event_dates': eventdate.event.eventDates()})
    else:
        return jsonify({'event_dates': eventdate.event.eventDates()})


# add a new date for an event
@event_dates_blueprint.route('/event/<int:id>/', methods=('POST',))
def add_eventdate(id):
    event = Event.query.get(id)
    if current_user.is_authenticated:
        # return is favorited
        pass
    else:
        return jsonify({'event_dates': eventdate.event.eventDates()})


# query all event dates
@event_dates_blueprint.route('/', methods=('GET',))
def fetch_events():
    start_time = time.time()

    if request.args.get('min'):
        min = datetime.utcfromtimestamp(int(request.args.get('min'))/1000)
    else:
        min = datetime.utcnow()
    if request.args.get('max') == 'Infinity':
        max = datetime.utcfromtimestamp(
            int(request.args.get('max'))/1000)  # two years from now
    elif request.args.get('max'):
        max = datetime.utcfromtimestamp(int(request.args.get('max'))/1000)
        print(request.args.get('max'))
    else:
        max = datetime.utcnow().replace(year=datetime.utcnow().year + 2)  # two years from now
    print(min)
    print(max)
    print('fuck')
    if request.args.get('location'):
        location = json.loads(request.args.get('location'))
        radii = [1000, 5000, 10000, 20000, 50000, 100000, 200000, 500000]
        event_dates = None
        print(location)
        lat = float(location['lat'])
        lon = float(location['lon'])
        wkt_element = WKTElement('POINT(%f %f)' % (lon, lat), 4326)
        # return event dates by location and add a distance column
        for radius in radii:
            print(radius)
            count = db.session.query(
                EventDate,
                func.ST_Distance(cast(EventLocation.geo, Geography(srid=4326)), cast(
                    'SRID=4326;POINT(%f %f)' % (lon, lat), Geography(srid=4326))).label('distance')
                # potentially faster to keep geometry type then convert degrees to meters.
                # when input is geography type it returns meters
            ).join(
                EventLocation
            ).join(
                EventDate.event
            ).filter(func.ST_DWithin(cast(EventLocation.geo, Geography(srid=4326)), cast('SRID=4326;POINT(%f %f)' % (lon, lat), Geography(srid=4326)), radius)
                     ).count()
            if count >= 5:
                print(count)
                event_dates = db.session.query(
                    EventDate,
                    func.ST_Distance(cast(EventLocation.geo, Geography(srid=4326)), cast(
                        'SRID=4326;POINT(%f %f)' % (lon, lat), Geography(srid=4326))).label('distance')
                    # potentially faster to keep geometry type then convert degrees to meters.
                    # when input is geography type it returns meters
                ).join(
                    EventLocation
                ).join(
                    EventDate.event
                ).filter(func.ST_DWithin(cast(EventLocation.geo, Geography(srid=4326)), cast('SRID=4326;POINT(%f %f)' % (lon, lat), Geography(srid=4326)), radius))
                break
                # using geography instead of geometry for 4326 dwithin function is much faster
                # could possibly increase performace with boolean use_spheroid = False at the cost of accuracy

        if event_dates is None:
            return jsonify({'message': 'No events in 500km radius'}), 204

        print('location filter')
        print(time.time() - start_time)
    else:
        event_dates = db.session.query(
            EventDate
        ).join(
            EventDate.location
        ).join(
            EventDate.event)
        # this used to be EventLocation.event - I don't know why? maybe I broke it

    # filter dates
    event_dates = event_dates.filter(
        or_(
            and_(EventDate.event_start_naive >= min, and_(
                EventDate.event_end_naive <= max, EventDate.event_end_naive >= min)),
            and_(EventDate.event_start_naive >= min, EventDate.event_start_naive <= max),
        )
    )

    # filter cancelled events out
    event_dates = event_dates.filter(
        EventDate.cancelled == False
    )

    ''' the old version of this query will filter any events happening in the range.
        this is kind of confusing for users. might be good for a 'happening now' type query
        for homepage.
        this version was more suitable when navigation was done with a slider, but I think
        it would also mean that the date list would get clogged up with 'in progress' events
        (which could feel spammy)
        event_dates = event_dates.filter(
                        or_(
                            and_(EventDate.event_end>min,EventDate.event_end<max),
                            and_(EventDate.event_start>min,and_(EventDate.event_end<max, EventDate.event_end>min)),
                            and_(EventDate.event_start>min,EventDate.event_start<max),
                            and_(EventDate.event_start<min, EventDate.event_end>max)
                            )
                        )
    '''
    print(event_dates.all())

    print(time.time() - start_time)

    # filter location
    # filter bounds if no location specified
    if request.args.get('bounds') and not request.args.get('location'):
        bounds = json.loads(request.args.get('bounds'))
        northEast = bounds['_northEast']
        southWest = bounds['_southWest']
        print(bounds)
        event_dates = event_dates.filter(
            and_(EventLocation.lat < northEast['lat'],
                 EventLocation.lat > southWest['lat'],
                 EventLocation.lng < northEast['lng'],
                 EventLocation.lng > southWest['lng']
                 )
        )
        print('bounds filter')
        print(time.time() - start_time)

    # filter tags
    if request.args.get('tags[]'):
        tags = request.args.getlist('tags[]')
        print(tags)
        for tag in tags:
            event_dates = event_dates.filter(
                or_(EventDate.artists.any(EventArtist.artist_name == tag),
                    Event.event_tags.any(EventTag.tag_id == tag)),
            )

    # order by date
    event_dates = event_dates.order_by(EventDate.event_start.asc())
    print('orderby date')
    print(time.time() - start_time)

    if request.args.get('page'):
        page = int(request.args.get('page'))
    else:
        page = 1

    # paginate
    event_dates_paginated = event_dates.paginate(page, per_page)

    print('paginate')
    print(time.time() - start_time)
    print(event_dates.all())

    if request.args.get('location'):
        print('location query')
        results = []
        for i in event_dates_paginated.items:
            result = i[0].minified()
            result['distance'] = int(i[1] / 1000)
            results.append(result)
            print('.', end="", flush=True)
        print('return')
        print(time.time() - start_time)
        return jsonify(results), 200

    return jsonify([e.minified() for e in event_dates_paginated.items]), 200

# get an eventdates revisions
@event_dates_blueprint.route('/<int:id>/revisions/', methods=('GET',))
def eventDateRevision(id):
    if request.method == 'GET':
        ed = EventDate.query.get(id)
        return jsonify(ed.revisions())

# get an eventdates revisions
@event_dates_blueprint.route('/<int:id>/', methods=('DELETE',))
def delete_eventdate(id):
    ed = EventDate.query.get(id)
    if ed is not None:
        db.session.delete(ed)
        db.session.commit()
        return '', 204


@event_dates_blueprint.route('/<int:id>/', methods=('PUT',))
@login_required
def update_eventdate(id):
    data = request.get_json()
    ed = EventDate.query.get(id)
    print(data)
    description = data.get('description')
    url = data.get('url')
    dateTime = data.get('dateTime')
    location = data.get('location')
    cancelled = data.get('cancelled')

    if cancelled is not None:
        ed.cancelled = cancelled
        if cancelled is False:
            # delete reason for deleting
            ed.description = ''

    if description:
        ed.description = description

    if url:
        ed.url = url

    if dateTime:
        if location:
            lat = location['geometry']['location']['lat']
            lng = location['geometry']['location']['lng']
        else:
            lat = ed.location.lat
            lng = ed.location.lng

        date = dateTime.get('date')
        geocode = reverse_geocode.search([(lat, lng)])[0]
        event_start = datetime.strptime(date['start'], '%Y-%m-%dT%H:%M:%S.%fZ')
        event_end = None
        all_day = True

        if date.get('end', None) is not None:
            print('has attr')
            event_end = datetime.strptime(date['end'], '%Y-%m-%dT%H:%M:%S.%fZ')

        # event start time is specified
        if dateTime.get('startHours', None) is not None:
            print('start date triggered')
            all_day = False
            event_start = event_start.replace(hour=int(dateTime.get('startHours')))
            if dateTime.get('startMinutes') is not None:
                event_start = event_start.replace(
                    minute=int(dateTime.get('startMinutes')))

        # event end time is specified
        if dateTime.get('endHours', None) is not None and event_end is not None:
            print('end date triggered')
            all_day = False
            event_end = event_end.replace(hour=int(dateTime.get('endHours')))
            if dateTime.get('endMinutes') is not None:
                event_end = event_end.replace(minute=int(dateTime.get('endMinutes')))
        #
        try:
            # ADD CORRECT TIMEZONE TO DATE TIME AND THEN CONVERT TO UTC
            tf = TimezoneFinder()
            tz = tf.timezone_at(lng=lng, lat=lat)
            tz_obj = timezone(tz)

        except UnknownTimeZoneError:
            print('TIMEZONE ERROR')
            pass  # {handle error}

        """
        Date should be received as a naive date
        ie. the local time where the event is happening with no tz info.
        """
        event_start = event_start.replace(tzinfo=None)
        event_start_naive = event_start
        event_start = tz_obj.localize(event_start)
        event_start = event_start.astimezone(utc)
        event_start = event_start.replace(tzinfo=None)
        event_end_naive = None
        if event_end is not None:
            event_end = event_end.replace(tzinfo=None)
            event_end_naive = event_end
            event_end = tz_obj.localize(event_end)
            event_end = event_end.astimezone(utc)
            event_end = event_end.replace(tzinfo=None)

        ed.event_start = event_start
        ed.event_end = event_end
        ed.event_start_naive = event_start_naive
        ed.event_end_naive = event_end_naive
        ed.all_day = all_day
        ed.tz = tz
        print('start naive')
        print(event_start_naive)
        print('end naive')
        print(event_end_naive)
        print('start')
        print(event_start)
        print('end')
        print(event_end)
        print(ed.to_dict())
    if location:
        lat = location['geometry']['location']['lat']
        lng = location['geometry']['location']['lng']
        location_name = location['name']
        location_description = location['description']
        location_types = location['types']
        location_place_id = location['place_id']

        geocode = reverse_geocode.search([(lat, lng)])[0]
        try:
            # ADD CORRECT TIMEZONE TO DATE TIME AND THEN CONVERT TO UTC
            tf = TimezoneFinder()
            tz = tf.timezone_at(lng=lng, lat=lat)
            tz_obj = timezone(tz)

        except UnknownTimeZoneError:
            print('TIMEZONE ERROR')
            pass  # {handle error}

        location_type_objects = []
        for t in location_types:
            elt = EventLocationType(type=t)
            db.session.merge(elt)
            location_type_objects.append(elt)

        location = EventLocation(geohash=pgh.encode(lat, lng),
                                 # For geodetic coordinates, X is longitude and Y is latitude
                                 geo='SRID=4326;POINT ({0} {1})'.format(lng, lat),
                                 name=location_name,
                                 description=location_description,
                                 types=location_type_objects,
                                 lat=lat,
                                 lng=lng,
                                 country_code=geocode['country_code'],
                                 city=geocode['city'],
                                 place_id=location_place_id)
        location = db.session.merge(location)
        ed.location = location
        ed.tz = tz
        # date settings not touched
        # update location of all future eventdates
    db.session.flush()
    activity = Activity(verb=u'update', object=ed, target=ed.event)
    # create_notification('UPDATE EVENT', activity, ed.event.followers)
    db.session.add(activity)
    db.session.commit()
    print(ed.to_dict())
    return jsonify(ed.to_dict()), 201
