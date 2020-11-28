"""
api.py
- provides the API endpoints for consuming and producing
  REST requests and responses
"""

from flask import Blueprint, jsonify, request, Flask, redirect, flash, url_for, current_app, send_from_directory
from pmapi.models.User import User
from pmapi.models.EventTag import EventTag, Tag
from pmapi.models.EventImage import EventImage
from pmapi.models.EventContribution import EventContribution
from pmapi.models.Event import Event
from pmapi.application import db
from pmapi.NearbyEvents import NearbyEvents
from .oauth import OAuthSignIn
from .config import BaseConfig
from functools import wraps
import logging
import traceback
from datetime import datetime, timedelta
import numpy as np
import jwt
import csv
import reverse_geocode
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
from PIL import Image, ImageOps
from io import BytesIO
import os

api = Blueprint('api', __name__)

app = Flask(__name__)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

#decorator function to verify user is authenticated
def token_required(f):
    @wraps(f)
    def _verify(*args, **kwargs):
        print(request.cookies.get('token'))

        auth_headers = request.headers.get('Authorization', '').split()
        print(auth_headers)
        invalid_msg = {
            'message': 'Invalid token. Registeration and / or authentication required',
            'authenticated': False
        }
        expired_msg = {
            'message': 'Expired token. Reauthentication required.',
            'authenticated': False
        }

        if len(auth_headers) != 2:

            return jsonify(invalid_msg), 401

        try:

            token = auth_headers[1]
            data = jwt.decode(token, current_app.config['SECRET_KEY'])
            user = User.query.filter_by(email=data['sub']).first()
            if not user:
                raise RuntimeError('User not found')

            return f(user, *args, **kwargs)
        except jwt.ExpiredSignatureError:
            app.logger.info('ExpiredSignatureError')
            print('ExpiredSignatureError')

            return jsonify(expired_msg), 401 # 401 is Unauthorized HTTP status code
        except (jwt.InvalidTokenError, Exception) as e:
            print(e)
            print(traceback.format_exc())
            return jsonify(invalid_msg), 401

    return _verify

#decorator function to check if user is logged in
def user_logged_in(f):
    @wraps(f)
    def _verify(*args, **kwargs):

        auth_headers = request.headers.get('Authorization', '').split()
        print(auth_headers)
        print(len(auth_headers))
        invalid_msg = {
            'message': 'Invalid token. Registeration and / or authentication required',
            'authenticated': False
        }
        expired_msg = {
            'message': 'Expired token. Reauthentication required.',
            'authenticated': False
        }

        if len(auth_headers)<=1 or auth_headers[1]=='null' or auth_headers[1]=='undefined':
            #user not logged in, return function without user id
            print("NO FUCKING AUTH HEADERS")
            return f(current_user=None, *args, **kwargs)

        try:
            token = auth_headers[1]
            data = jwt.decode(token, current_app.config['SECRET_KEY'])
            user = User.query.filter_by(email=data['sub']).first()
            if not user:
                raise RuntimeError('User not found')

            return f(user, *args, **kwargs,)
        except jwt.ExpiredSignatureError:
            app.logger.info('ExpiredSignatureError')
            print('ExpiredSignatureError')

            return jsonify(expired_msg), 401 # 401 is Unauthorized HTTP status code
        except (jwt.InvalidTokenError, Exception) as e:
            print(e)
            print(traceback.format_exc())
            return jsonify(invalid_msg), 401

    return _verify

#update event by ID number
@api.route('/event/<int:id>', methods=('PUT',))
@token_required
def update_event(current_user, id):

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
@token_required
def voteEventTag(current_user, eventid, tag):
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
@token_required
def voteImage(current_user, imageid):
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
@token_required
def voteContribution(current_user, contributionid):
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
@user_logged_in
def fetch_events_near(current_user, lat, lng):

    if current_user:
        results=NearbyEvents.search([(lat,lng)], current_user)
    else:
        results=NearbyEvents.search([(lat,lng)])

    return jsonify(results)

#get event by ID number
@api.route('/event/<int:id>', methods=('GET',))
@user_logged_in
def event(current_user, id):

    event = Event.query.get(id)
    print(str(current_user)+'currentuser')
    if current_user:
        return jsonify({ 'event': event.to_dict(current_user.id)})
    else:
        return jsonify({ 'event': event.to_dict()})

#get all events
@api.route('/events/', methods=('GET',))
def fetch_events():
    events = Event.query.all()
    return jsonify ([e.to_dict() for e in events]), 201

#get users favorite events
@api.route('/favorites/', methods=('GET',))
@token_required
def fetch_favorites(current_user):
    if not current_user:
        return jsonify({ 'message': 'Not authenticated', }), 401
    return jsonify ([e.to_dict() for e in current_user.favorite_events]), 201

#toggle whether or not this event is faved by current user
@api.route('/favorite/<int:id>', methods=('PUT',))
@token_required
def toggle_favorite(current_user, id):
    event = Event.query.get(id)
    if not event:
        return jsonify({ 'message': 'Event not found', }), 401
    if current_user in event.favorited_by:
        event.favorited_by.remove(current_user)
    else:
        event.favorited_by.append(current_user)
    print(event)

    db.session.merge(event)
    db.session.commit()
    user = User.query.get(current_user.id)
    print(user.favorite_events)
    #COMPLETE THIS
    return jsonify([e.to_dict() for e in user.favorite_events]), 201

#add new event
@api.route('/events/', methods=('POST',))
@token_required
def create_event(current_user):
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

@api.route('/register/', methods=('POST',))
def register():
    data = request.get_json()
    user = User(**data)
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_dict()), 201

@api.route('/login/', methods=['GET', 'POST'])
@user_logged_in
def login(current_user):
    if request.method == 'POST':
        data = request.get_json()
        user = User.authenticate(**data)

        if not user:
            return jsonify(message='Invalid credentials', authenticated=False), 401

        token = jwt.encode({
            'sub': user.email,
            'iat':datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(days=30)},
            current_app.config['SECRET_KEY'])
        return jsonify(token=token.decode('UTF-8'), user=user.to_dict()), 201

    if request.method == 'GET':
        if current_user:
                return jsonify(user=current_user.to_dict(), authenticated=True), 201

        else:
                return jsonify(message='No login token', authenticated=False ), 401
