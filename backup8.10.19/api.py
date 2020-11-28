"""
api.py
- provides the API endpoints for consuming and producing
  REST requests and responses
"""

from flask import Blueprint, jsonify, request, Flask, redirect, flash, url_for, current_app, send_from_directory
from pmapi.models.User import User
from pmapi.models.EventTag import EventTag, Tag
from pmapi.models.EventArtist import Artist, EventArtist
from pmapi.models.EventImage import EventImage
from pmapi.models.Event import Event, Rrule, EventDate
from pmapi.application import db, lm
from pmapi.NearbyEvents import NearbyEvents
from .oauth import OAuthSignIn
from .config import BaseConfig
from functools import wraps
import logging
import json
import traceback
from datetime import datetime, timedelta
from dateutil.rrule import *
import numpy as np
import jwt
import csv
import reverse_geocode
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from PIL import Image, ImageOps
from io import BytesIO
import time
import os

api = Blueprint('api', __name__)

app = Flask(__name__)

#pagination quantity
quantity = 50

def filterEvents(x, min, max):
    if hasattr(x, 'event_end') and x.event_end is not None:
        print('has end')
        if (x.event_end > min and x.event_end < max) or (x.event_start > min and x.event_end < max) or (x.event_start > min and x.event_start < max) or (x.event_start < min and x.event_end > max):
            return True
        else:
            return False
    #handle case where there is no enddate
    else:
        if (x.event_start > min and x.event_start < max):
            return True
        else:
            return False

def filterEventsBounds(x, northEast, southWest, min, max):
    if hasattr(x, 'event_end') and x.event_end is not None:
        print('has end')
        if (x.lat<northEast['lat'] and x.lat>southWest['lat'] and x.lng<northEast['lng'] and x.lng>southWest['lng'] and ((x.event_end > min and x.event_end < max) or (x.event_start > min and x.event_end < max) or (x.event_start > min and x.event_start < max) or (x.event_start < min and x.event_end > max))):
            return True
        else:
            return False
    #handle case where there is no enddate
    else:
        if (x.lat<northEast['lat'] and x.lat>southWest['lat'] and x.lng<northEast['lng'] and x.lng>southWest['lng'] and (x.event_start > min and x.event_start < max)):
            return True
        else:
            return False

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@lm.user_loader
def load_user(user_id):
    print('load_user called')
    user = User.query.get(user_id)
    print('user loaded')
    return user

#update event by ID number
@api.route('/event/<int:id>', methods=('PUT',))
@login_required
def update_event(id):

    data = request.get_json()
    event_date = EventDate.query.get(id)

    if data['update_all'] is True:
        #update all events
        pass
    else:
        if 'event_artists' in data:
            for a in data['event_artists']:
                artist = Artist(name=a)
                #check if tag is already in db
                if db.session.query(Artist).filter(Artist.name==a).count():
                    artist = db.session.query(Artist).filter(Artist.name==a).one()
                ea = EventArtist(artist=artist, event_date=event_date)
                db.session.add(ea)
        if 'description' in data:
            event_date.description = data['description']
        if 'url' in data:
            event_date.url = data['url']
        if 'lat' in data and 'lng' in data and 'city' in data and 'country' in data and 'country_code' in data:
            event_date.lat = data['lat']
            event_date.lng = data['lng']
            event_date.city = data['city']
            event_date.country = data['country']
            event_date.country_code = data['country_code']

    if(data!=None):
        event.description = data['description']
        db.session.commit()
        return jsonify({ 'event': event.to_dict() })
'''
    if(request.files['file']):
        file = request.files['file']
        print(request.files['file'])
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(current_app.config['IMAGE_UPLOAD_FOLDER'], filename))
            thumb = ImageOps.fit(
                Image.open(os.path.join(current_app.config['IMAGE_UPLOAD_FOLDER'], filename)),
                (256, 256),
                Image.ANTIALIAS)
            file_extension = os.path.splitext(filename)[1][1:]
            #stupid library is stupid and only recognises 'jpeg'
            if file_extension == "jpg" or file_extension == "JPG":
                file_extension = 'JPEG'
            print('thumbformat:' + file_extension)

            thumbfilename = os.path.splitext(filename)[0] + "_thumb" + '.' + file_extension
            print('filename: ' + filename)
            print('thumbfilename:' + file_extension)
            thumb.save(os.path.join(current_app.config['IMAGE_UPLOAD_FOLDER'], thumbfilename), file_extension)

            event_image = EventImage()
            event_image.filename=filename
            event_image.thumb_filename=thumbfilename
            event_image.user_id=current_user.id
            event_image.event_id=id
            db.session.merge(event_image)
            db.session.commit()
            return jsonify({'event_image': event_image.to_dict()}), 201
'''
#EventTag vote
@api.route('/event/<int:eventid>/<string:tag>', methods=('PUT',))
@login_required
def voteEventTag( eventid, tag):
    data = request.get_json()
    vote = int(data['vote'])
    #et = db.session.query(EventTag).get((tag, eventid))
    eventtag = EventTag.query.get_or_404((tag, int(eventid)))
    vote_status = eventtag.vote(user_id=current_user.id, vote=vote)
    if not vote:
        abort(404)
    #check if contribution has been voted by user yet or not
    return jsonify(new_votes=eventtag.votes, vote_status=vote_status)

#Image vote
@api.route('/image/<int:imageid>', methods=('PUT',))
@login_required
def voteImage(imageid):
    data = request.get_json()
    vote = int(data['vote'])

    # contribution = db.session.query(EventContribution).get(contributionid)
    eventimage = EventImage.query.get_or_404(int(imageid))
    if not vote:
        abort(404)
    vote_status = eventimage.vote(user_id=current_user.id, vote=vote)

    #check if contribution has been voted by user yet or not
    return jsonify(new_votes=eventimage.votes, vote_status=vote_status)

#Contribution vote
@api.route('/contribution/<int:contributionid>', methods=('PUT',))
@login_required
def voteContribution(contributionid):
    data = request.get_json()
    vote = int(data['vote'])
    # contribution = db.session.query(EventContribution).get(contributionid)
    contribution = EventContribution.query.get_or_404(int(contributionid))
    if not vote:
        abort(404)
    vote_status = contribution.vote(user_id=current_user.id, vote=vote)

    #check if contribution has been voted by user yet or not
    return jsonify(new_votes=contribution.votes, vote_status=vote_status)

#get nearby events
@api.route('/events/<string:lat>/<string:lng>', methods=('GET',))
def fetch_events_near(lat, lng):

    if current_user.is_authenticated:
        results=NearbyEvents.search([(lat,lng)], current_user)
    else:
        results=NearbyEvents.search([(lat,lng)])

    return jsonify(results)

#get event by ID number
@api.route('/event/<int:id>', methods=('GET',))
def event(id):
    event = EventDate.query.get(id)
    print('t')
    if current_user.is_authenticated:
        print('1')
        return jsonify({ 'event': event.to_dict(current_user)})
    else:
        return jsonify({ 'event': event.to_dict()})

#event query UNUSED
# tags[], int min, int max
@api.route('/events/query/', methods=('GET',))
def fetch_events():

    # NOTES FOR NEW version
    # First I need to query all event dates for events (or date range if applicable)
    # Then I need to filter these eevents by tags
    #tags
    #bounds
    #minmax
    data = request.get_json()

    event_dates = []
    if request.args.get('min'):
        min = datetime.fromtimestamp(int(request.args.get('min'))/1000)
    else: min = datetime.fromtimestamp(time.time())
    if request.args.get('max') == 'Infinity':
        max = datetime.fromtimestamp(time.time()+(86400000*730)) #two years from now
    elif request.args.get('max'):
        max = datetime.fromtimestamp(int(request.args.get('max'))/1000)
    else: max = datetime.fromtimestamp(time.time()+(86400000*730)) #two years from now

    northEast = {}
    southWest = {}
    page = int(request.args.get('page'))
    print(request.args)
    #this needs to change to give an EXACT match
    if request.args.get('tags[]'):
        for t in request.args.getlist('tags[]'):
            print(t)
            event_tags = db.session.query(Tag).filter(Tag.tag==t).one().events_with_tag
            for et in event_tags:
                for ed in et.event.event_dates:
                    event_dates.append(ed)
    else:
        event_dates = db.session.query(EventDate).all()

    if request.args.get('bounds'):
        bounds = json.loads(request.args.get('bounds'))
        filterobj = filter(lambda x: filterEventsBounds(x, bounds['_northEast'], bounds['_southWest'], min, max), event_dates)

    else: filterobj = filter(lambda x: filterEvents(x, min, max), event_dates)
    event_dates = list(filterobj)


    #pagination
    print(event_dates)
    print(page)
    if page == 0:
            return jsonify([e.to_dict() for e in event_dates[0: quantity]]), 200
    if page * quantity > len(events):
            print("No more events")
            return jsonify({}), 200
    else:
            return jsonify([e.to_dict() for e in event_dates[page * quantity: page * quantity + quantity]]), 200

#get all event points
@api.route('/points/', methods=('GET',))
def fetch_points():
    event_dates = []
    if request.args.get('min'):
        min = datetime.fromtimestamp(int(request.args.get('min'))/1000)
    else: min = datetime.fromtimestamp(time.time())
    if request.args.get('max') == 'Infinity':
        max = datetime.fromtimestamp(time.time()+(86400000*730)) #two years from now
    elif request.args.get('max'):
        max = datetime.fromtimestamp(int(request.args.get('max'))/1000)
    else: max = datetime.fromtimestamp(time.time()+(86400000*730)) #two years from now

    #this needs to change to give an EXACT match
    if request.args.get('tags'):
        for t in request.args.get('tags'):
            event_tags = db.session.query(Tag).filter(Tag.tag==t.text).one().events_with_tag
            for et in event_tags:
                event_dates.append(et.event_date)
    else:
        event_dates = db.session.query(EventDate).all()

    filterobj = filter(lambda x: filterEvents(x, min, max), event_dates)
    event_dates = list(filterobj)

    event_ids = []
    next_eventdates = []
    for event in event_dates:
        if event.event_id not in event_ids:
            next_eventdates.append(event.event.nextEvent())
            event_ids.append(event.event_id)

    return jsonify ([e.minified() for e in next_eventdates]), 201

#get users favorite events
@api.route('/favorites/', methods=('GET',))
@login_required
def fetch_favorites():
    print(current_user)
    if not current_user.is_authenticated:
        return jsonify({ 'message': 'Not authenticated', }), 401
    return jsonify ([e.to_dict() for e in current_user.get_favorites()]), 201

#toggle whether or not this event is faved by current user
@api.route('/favorite/<int:id>', methods=('PUT',))
@login_required
def toggle_favorite(id):
    event = Event.query.get_or_404(int(id))

    fav_state = event.favorite(user_id=current_user.id)
    print(event)
    print(fav_state)
    return jsonify(fav_status=fav_state)

#add new event
@api.route('/events/', methods=('POST',))
@login_required
def create_event():
    data = request.get_json()

    geocode = reverse_geocode.search([(data['lat'],data['lng'])])[0]

    event_start = datetime.fromtimestamp(int(data['event_start']) / 1000.0)
    event_end = None
    all_day = True
    if 'event_end' in data and data['event_end'] is not None:
        event_end = datetime.fromtimestamp(int(data['event_end']) / 1000.0)

    if 'start_am_pm' in data is not None and 'start_hours' in data is not None:
        print(data['start_minutes'])
        all_day=False
        if data['start_am_pm'] is 'am':
            event_start.replace(hour=int(data['start_hours']))
        if data['start_am_pm'] is 'pm':
            event_start.replace(hour=int(data['start_hours'])+12)
        if data['start_minutes'] is not None:
            event_start.replace(minute=int(data['start_minutes']))
    if 'end_am_pm' in data is not None and 'end_hours' in data is not None and 'event_end' in data is not None:
        all_day=False
        if data['end_am_pm'] is 'am':
            event_end.replace(hour=int(data['end_hours']))
        if data['end_am_pm'] is 'pm':
            event_end.replace(hour=int(data['end_hours'])+12)
        if data['end_minutes'] is not None:
            event_end.replace(minute=int(data['end_minutes']))
    #the end date is optional, so if there is no end date set event_end to be todays date then adjust the time to the end time
    elif 'end_am_pm' in data is not None and 'end_hours' in data is not None and 'event_end' is None:
        all_day=False
        event_end = datetime.fromtimestamp(int(data['event_start']) / 1000.0)
        if data['end_am_pm'] is 'am':
            event_end.replace(hour=int(data['end_hours']))
        if data['end_am_pm'] is 'pm':
            event_end.replace(hour=int(data['end_hours'])+12)
        if data['end_minutes'] is not None:
            event_end.replace(minute=int(data['end_minutes']))

    event = Event(name=data['name'],
    creator_id=current_user.id)

    for t in data['event_tags']:
        tag = Tag(tag=t)
        #check if tag is already in db
        if db.session.query(Tag).filter(Tag.tag==t).count():
            tag = db.session.query(Tag).filter(Tag.tag==t).one()
        et = EventTag(tag=tag, event=event)
        db.session.add(et)

    #merging - is this ok?
    event = db.session.merge(event)
    db.session.flush()

    #handle recurring events
    if 'separation_count' in data:
        print('separation in data')
        if data['separation_count'] != 10:
            startdates = []
            enddates = []
            print(data)
            if 'week_of_month' in data:
                two_years_away = event_start.replace(year=event_start.year+2)
                if int(float(data['recurrence_type'])) == 2:
                    #monthly recurring event
                    print('monthly recurring event')
                    startdates = list(rrule(MONTHLY, interval=data['separation_count'], byweekday=data['day_of_week'](data['week_of_month']), dtstart=event_start, until=two_years_away))
                    enddates = list(rrule(MONTHLY, interval=data['separation_count'], byweekday=data['day_of_week'](data['week_of_month']), dtstart=event_end, until=two_years_away))
                    rp = Rrule(
                        event_id=event.id,
                        recurring_type=data['recurrence_type'],
                        separation_count=data['separation_count'],
                        day_of_week=data['day_of_week'],
                        week_of_month=data['week_of_month']
                    )
                    db.session.add(rp)
                elif data['recurrence_type'] == 3:
                    #yearly recurring event
                    print('yearly recurring event')
                    startdates = list(rrule(YEARLY, interval=data['separation_count'], bymonth=data['month_of_year'], byweekday=data['day_of_week'](data['week_of_month']), dtstart=event_start, until=two_years_away))
                    enddates = list(rrule(YEARLY, interval=data['separation_count'], bymonth=data['month_of_year'], byweekday=data['day_of_week'](data['week_of_month']), dtstart=event_end, until=two_years_away))
                    rp = Rrule(
                        event_id=event.id,
                        recurring_type=data['recurrence_type'],
                        separation_count=data['separation_count'],
                        day_of_week=data['day_of_week'],
                        week_of_month=data['week_of_month'],
                        month_of_year=data['month_of_year']
                    )
                    db.session.add(rp)

            elif 'day_of_week' in data:
                print('weekly recurring event')
                startdates = list(rrule(WEEKLY, interval=data['separation_count'], byweekday=data['day_of_week'], dtstart=event_start, until=two_years_away))
                enddates = list(rrule(WEEKLY, interval=data['separation_count'], byweekday=data['day_of_week'], dtstart=event_end, until=two_years_away))
                rp = Rrule(
                    event_id=event.id,
                    recurring_type=data['recurrence_type'],
                    separation_count=data['separation_count'],
                    day_of_week=data['day_of_week'],
                )
                db.session.add(rp)
            else:
                #absolute date type specified
                #if monthly recurrance
                if data['recurrence_type'] == 2:
                    print('absolute monthly event')
                    startdates = list(rrule(MONTHLY, interval=data['separation_count'], bymonth=data['month_of_year'], bymonthday=data['day_of_month'],  dtstart=event_start, until=two_years_away))
                    enddates = list(rrule(MONTHLY, interval=data['separation_count'], bymonth=data['month_of_year'], bymonthday=data['day_of_month'],  dtstart=event_end, until=two_years_away))
                    rp = Rrule(
                        event_id=event.id,
                        recurring_type=data['recurrence_type'],
                        separation_count=data['separation_count'],
                        day_of_month=data['day_of_month'],
                    )
                    db.session.add(rp)
                #yearly recurrance
                elif data['recurrence_type'] == 3:
                    print('absolute yearly event')
                    startdates = list(rrule(YEARLY, interval=data['separation_count'], bymonth=data['month_of_year'], bymonthday=data['day_of_month'], dtstart=event_start, until=two_years_away))
                    enddates = list(rrule(YEARLY, interval=data['separation_count'], bymonth=data['month_of_year'], bymonthday=data['day_of_month'], dtstart=event_end, until=two_years_away))
                    rp = Rrule(
                        event_id=event.id,
                        recurring_type=data['recurrence_type'],
                        separation_count=data['separation_count'],
                        day_of_month=data['day_of_month'],
                        month_of_year=data['month_of_year']
                    )
                    db.session.add(rp)
            event.recurring = True
            for start, end in zip(startdates, enddates):
                ed = EventDate(
                    event_id=event.id,
                    event=event,
                    event_end=end,
                    event_start=start,
                    all_day=all_day,
                    description=data['description'],
                    url=data['url'],
                    lat=data['lat'],
                    lng=data['lng'],
                    country_code=geocode['country_code'],
                    country=geocode['country'],
                    city=geocode['city'],
                )
                NearbyEvents.addEventToCSV(ed.lat, ed.lng, ed.id)
                db.session.add(ed)
                print('ed recurr added')

        else:
            #event is a one-off
            event.recurring = False
            ed = EventDate(
                    event_id=event.id,
                    event=event,
                    event_end=event_end,
                    event_start=event_start,
                    all_day=all_day,
                    description=data['description'],
                    url=data['url'],
                    lat=data['lat'],
                    lng=data['lng'],
                    country_code=geocode['country_code'],
                    country=geocode['country'],
                    city=geocode['city'],
                    )
            db.session.add(ed)
            NearbyEvents.addEventToCSV(ed.lat, ed.lng, ed.id)
            print('ed one-off added')

    db.session.commit()

    return jsonify(event.to_dict()), 201

#upload image NOT TESTED YET
@app.route('/image/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'image' not in request.files:
            flash('No file part')
            return redirect(request.url)
        image = request.files['image']
        # if user does not select file, browser also
        # submit a empty part without filename
        if image.filename == '':
            flash('No selected file')
            return redirect(request.url)
        elif image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('uploaded_file', filename=filename))

#get image by ID
@app.route('/photo/<id>', methods=('GET',))
def show(id):
    image = images.load(id)
    if image is None:
        abort(404)
    url = images.url(image.filename)
    return jsonify(url), 201

#get all tags
@api.route('/tags/', methods=('GET',))
def tags():
    if request.method == 'GET':
        tags = Tag.query.all()
        tagsdict = [t.to_dict() for t in tags]
        return jsonify (tagsdict)

#get all artists
@api.route('/artists/', methods=('GET',))
def artists():
    if request.method == 'GET':
        artists = Artist.query.all()
        artistsdict = [a.to_dict() for a in artists]
        return jsonify (artistsdict)

@api.route('/register/', methods=('POST',))
def register():
    data = request.get_json()
    user = User(**data)
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_dict()), 201

@api.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        user = User.authenticate(**data)

        if not user:
            return jsonify(message='Invalid credentials', authenticated=False), 401

        #flask-login
        login_user(user, remember=True)
        print(current_user)

        #am I vulnerable to open redirects?
        return jsonify(user=user.to_dict(), authenticated=True), 201

    if request.method == 'GET':
        if current_user.is_authenticated:
                return jsonify(user=current_user.to_dict(), authenticated=True), 201

        else:
                return jsonify(message='No login token', authenticated=False ), 401

@api.route('/logout/', methods=['POST'])
@login_required
def logout():
    logout_user()
    return ('', 201)
