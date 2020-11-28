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
from pmapi.models.EventContribution import EventContribution
from pmapi.models.Event import Event
from pmapi.application import db, lm
from pmapi.NearbyEvents import NearbyEvents
from .oauth import OAuthSignIn
from .config import BaseConfig
from functools import wraps
import logging
import json
import traceback
from datetime import datetime, timedelta
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
    if (x.event_end > min and x.event_end < max) or (x.event_start > min and x.event_end < max) or (x.event_start > min and x.event_start < max) or (x.event_start < min and x.event_end > max):
        return True
    else:
        return False

def filterEventsBounds(x, northEast, southWest, min, max):
    if (x.lat<northEast['lat'] and x.lat>southWest['lat'] and x.lng<northEast['lng'] and x.lng>southWest['lng'] and ((x.event_end > min and x.event_end < max) or (x.event_start > min and x.event_end < max) or (x.event_start > min and x.event_start < max) or (x.event_start < min and x.event_end > max))):
        return True
    else: return False

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
    event = Event.query.get(id)

    if(data!=None):
        event.description = data['description']
        db.session.commit()
        return jsonify({ 'event': event.to_dict() })

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
    event = Event.query.get(id)
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
    #tags
    #bounds
    #minmax
    events = []
    if request.args.get('min'):
        min = float(request.args.get('min'))
    else: min = time.time()*1000
    if request.args.get('max'):
        max = float(request.args.get('max'))
    else: max = time.time()*1000+(86400000*730) #two years from now
    northEast = {}
    southWest = {}
    page = int(request.args.get('page'))

    #this needs to change to give an EXACT match
    if request.args.get('tags'):
        for t in request.args.get('tags'):
            event_tags = db.session.query(Tag).filter(Tag.tag==t.text).one().events_with_tag
            for et in event_tags:
                events.append(et.event)
    else:
        events = db.session.query(Event).all()

    if request.args.get('bounds'):
        bounds = json.loads(request.args.get('bounds'))
        filterobj = filter(lambda x: filterEventsBounds(x, bounds['_northEast'], bounds['_southWest'], min, max), events)

    else: filterobj = filter(lambda x: filterEvents(x, min, max), events)
    events = list(filterobj)

    #pagination
    print(events)
    if page == 0:
            return jsonify([e.to_dict() for e in events[0: quantity]]), 200
    if page * quantity > len(events):
            print("No more events")
            return jsonify({}), 200
    else:
            return jsonify(events=[e.to_dict() for e in events[page * quantity: page * quantity + quantity]]), 200

#get all event points
@api.route('/points/', methods=('GET',))
def fetch_points():
    events = []
    if request.args.get('min'):
        min = float(request.args.get('min'))
    else: min = time.time()*1000
    if request.args.get('max'):
        max = float(request.args.get('max'))
    else: max = time.time()*1000+(86400000*730) #two years from now

    #this needs to change to give an EXACT match
    if request.args.get('tags'):
        for t in request.args.get('tags'):
            event_tags = db.session.query(Tag).filter(Tag.tag==t.text).one().events_with_tag
            for et in event_tags:
                events.append(et.event)
    else:
        events = Event.query.all()


    filterobj = filter(lambda x: filterEvents(x, min, max), events)
    events = list(filterobj)

    return jsonify ([e.minified() for e in events]), 201


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

    event = Event(name=data['name'],
    description=data['description'],
    url=data['url'],
    lat=data['lat'],
    lng=data['lng'],
    country_code=geocode['country_code'],
    country=geocode['country'],
    city=geocode['city'],
    event_start=data['event_start'],
    event_end=data['event_end'],
    creator_id=current_user.id)

    for t in data['event_tags']:
        tag = Tag(tag=t)
        #check if tag is already in db
        if db.session.query(Tag).filter(Tag.tag==t).count():
            tag = db.session.query(Tag).filter(Tag.tag==t).one()
        et = EventTag(tag=tag, event=event)
        db.session.add(et)

    for a in data['artists']:
        artist = Artist(name=a)
        #check if tag is already in db
        if db.session.query(Artist).filter(Artist.name==a).count():
            artist = db.session.query(Artist).filter(Artist.name==a).one()
        ea = EventArtist(artist=artist, event=event)
        db.session.add(ea)

    #merging - is this ok?
    event = db.session.merge(event)
    db.session.flush()
    NearbyEvents.addEventToCSV(event.lat, event.lng, event.id)

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
