from flask import Blueprint, Response, request, jsonify
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    current_user,
    login_required,
)
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
import pmapi.event_date.controllers as event_dates


per_page = 20

event_dates_blueprint = Blueprint("event_dates", __name__)

Activity = activity_plugin.activity_cls


# get all event_date for an event
@event_dates_blueprint.route("/event/<int:id>/", methods=("GET",))
def eventdates(id):
    eventdate = Event.query.get(id).event_dates

    if current_user.is_authenticated:
        # return is favorited
        return jsonify({"event_dates": eventdate.event.eventDates()})
    else:
        return jsonify({"event_dates": eventdate.event.eventDates()})


# add a new date for an event
@event_dates_blueprint.route("/event/<int:id>/", methods=("POST",))
def add_eventdate(id):
    event = Event.query.get(id)
    if current_user.is_authenticated:
        # return is favorited
        pass
    else:
        return jsonify({"event_dates": eventdate.event.eventDates()})


# query all event dates
@event_dates_blueprint.route("/", methods=("GET",))
def fetch_event_dates():

    min = request.args.get("min", None)
    max = request.args.get("max", None)
    location = request.args.get("location", None)
    bounds = request.args.get("bounds", None)
    tags = request.args.get("tags[]", None)
    page = request.args.get("page", None)

    if tags:
        tags = request.args.getlist("tags[]")

    if page:
        page = int(request.args.get("page"))

    results = event_dates.query_event_dates(min, max, location, bounds, tags, page)

    return jsonify(results), 200


# get an eventdates revisions
@event_dates_blueprint.route("/<int:id>/revisions/", methods=("GET",))
def eventDateRevision(id):
    if request.method == "GET":
        ed = EventDate.query.get(id)
        return jsonify(ed.revisions())


# get an eventdates revisions
@event_dates_blueprint.route("/<int:id>/", methods=("DELETE",))
def delete_eventdate(id):
    ed = EventDate.query.get(id)
    if ed is not None:
        db.session.delete(ed)
        db.session.commit()
        return "", 204


@event_dates_blueprint.route("/<int:id>/", methods=("PUT",))
@login_required
def update_eventdate(id):
    data = request.get_json()
    ed = EventDate.query.get(id)
    print(data)
    description = data.get("description")
    url = data.get("url")
    dateTime = data.get("dateTime")
    location = data.get("location")
    cancelled = data.get("cancelled")

    if cancelled is not None:
        ed.cancelled = cancelled
        if cancelled is False:
            # delete reason for deleting
            ed.description = ""

    if description:
        ed.description = description

    if url:
        ed.url = url

    if dateTime:
        if location:
            lat = location["geometry"]["location"]["lat"]
            lng = location["geometry"]["location"]["lng"]
        else:
            lat = ed.location.lat
            lng = ed.location.lng

        date = dateTime.get("date")
        geocode = reverse_geocode.search([(lat, lng)])[0]
        event_start = datetime.strptime(date["start"], "%Y-%m-%dT%H:%M:%S.%fZ")
        event_end = None
        all_day = True

        if date.get("end", None) is not None:
            print("has attr")
            event_end = datetime.strptime(date["end"], "%Y-%m-%dT%H:%M:%S.%fZ")

        # event start time is specified
        if dateTime.get("startHours", None) is not None:
            print("start date triggered")
            all_day = False
            event_start = event_start.replace(hour=int(dateTime.get("startHours")))
            if dateTime.get("startMinutes") is not None:
                event_start = event_start.replace(
                    minute=int(dateTime.get("startMinutes"))
                )

        # event end time is specified
        if dateTime.get("endHours", None) is not None and event_end is not None:
            print("end date triggered")
            all_day = False
            event_end = event_end.replace(hour=int(dateTime.get("endHours")))
            if dateTime.get("endMinutes") is not None:
                event_end = event_end.replace(minute=int(dateTime.get("endMinutes")))
        #
        try:
            # ADD CORRECT TIMEZONE TO DATE TIME AND THEN CONVERT TO UTC
            tf = TimezoneFinder()
            tz = tf.timezone_at(lng=lng, lat=lat)
            tz_obj = timezone(tz)

        except UnknownTimeZoneError:
            print("TIMEZONE ERROR")
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
        print("start naive")
        print(event_start_naive)
        print("end naive")
        print(event_end_naive)
        print("start")
        print(event_start)
        print("end")
        print(event_end)
        print(ed.to_dict())
    if location:
        lat = location["geometry"]["location"]["lat"]
        lng = location["geometry"]["location"]["lng"]
        location_name = location["name"]
        location_description = location["description"]
        location_types = location["types"]
        location_place_id = location["place_id"]

        geocode = reverse_geocode.search([(lat, lng)])[0]
        try:
            # ADD CORRECT TIMEZONE TO DATE TIME AND THEN CONVERT TO UTC
            tf = TimezoneFinder()
            tz = tf.timezone_at(lng=lng, lat=lat)
            tz_obj = timezone(tz)

        except UnknownTimeZoneError:
            print("TIMEZONE ERROR")
            pass  # {handle error}

        location_type_objects = []
        for t in location_types:
            elt = EventLocationType(type=t)
            db.session.merge(elt)
            location_type_objects.append(elt)

        location = EventLocation(
            geohash=pgh.encode(lat, lng),
            # For geodetic coordinates, X is longitude and Y is latitude
            geo="SRID=4326;POINT ({0} {1})".format(lng, lat),
            name=location_name,
            description=location_description,
            types=location_type_objects,
            lat=lat,
            lng=lng,
            country_code=geocode["country_code"],
            city=geocode["city"],
            place_id=location_place_id,
        )
        location = db.session.merge(location)
        ed.location = location
        ed.tz = tz
        # date settings not touched
        # update location of all future eventdates
    db.session.flush()
    activity = Activity(verb=u"update", object=ed, target=ed.event)
    # create_notification('UPDATE EVENT', activity, ed.event.followers)
    db.session.add(activity)
    db.session.commit()
    print(ed.to_dict())
    return jsonify(ed.to_dict()), 201
