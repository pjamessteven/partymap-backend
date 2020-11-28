from flask import Blueprint, Response, request, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from sqlalchemy import or_, and_

from pmapi.event.model import *
from pmapi.event_artist.model import *
from pmapi.event_tag.model import *

report_blueprint = Blueprint('report', __name__)

# report event_date artist
@login_required
@report_blueprint.route('/', methods=('POST',))
def report():
    event_id = None
    event_date_id = None
    event_location_geo = None
    event_artist = None
    event_tag = None
    event_contribution_id = None
    event_image_id = None
    user = None
    ip = None

    # for when this is running on nginx (https://stackoverflow.com/questions/3759981/get-ip-address-of-visitors-using-flask-for-python)
    if request.environ['REMOTE_ADDR']:
        print('IP not found?')
        ip = request.environ['REMOTE_ADDR']

    if request.args.get('event_id'):
        event = Event.query().get(request.args.get('event_id'))
        event_id = event.id
        user = event.creator_id

    if request.args.get('event_date_id'):
        event_date = EventDate.query().get(request.args.get('event_date_id'))
        event_date_id = event_date.id
        event_id = event_date.event.id
        user = event_date.creator_id

    if request.args.get('event_tag'):
        event_tag = EventTag.query.all().filter(and_(tag==request.args.get('event_tag'), event_id==event_id)).first()
        event_id = event_tag.event_id
        event_tag = event_tag.tag
        user = event_date.creator_id

    if request.args.get('event_artist'):
        event_artist = EventArtist.query.all().filter(and_(artist_name==request.args.get('event_artist'), event_date_id==event_date_id)).first()
        user = event_date.creator_id

    if request.args.get('event_contribution_id'):
        event_contribution = EventContribution.query.get(request.args.get('event_contribution_id'))
        event_contribution_id = event_contribution.id
        event_id = event_contribution.event_id
        user = event_contribution.creator_id

    if request.args.get('event_image_id'):
        event_image = EventImage.query.get(request.args.get('event_image_id'))
        event_image_id = event_image.id
        user = event_image.creator_id

    report = Report(
        event_tag=event_tag,
        event_artist=event_artist,
        event_date=event_date_id,
        event_image_id=event_image_id,
        event_contribution_id=event_contribution_id,
        event_location_geo=event_location_geo,
        event=event_id,
        creator=current_user.id,
        creator_ip=ip,
        reason_text=request.args.get('reason_text'),
        user=user)

    db.session.add(report)
    # ADD EMAIL ACTION HERE
    db.session.commit()
    return jsonify('Report reported'), 201
