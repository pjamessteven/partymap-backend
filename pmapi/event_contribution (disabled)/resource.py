from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required

from pmapi.extensions import db
from pmapi.event.model import Event
from pmapi.event_album.model import EventImage
from pmapi.event_contribution.model import EventContribution
from pmapi.exceptions import InvalidUsage, InvalidAPIRequest
from pmapi.event_album import controllers as event_images
from pmapi.report.model import Report

from .controllers import add_contribution
event_contribution_blueprint = Blueprint('event_contribution', __name__)


@event_contribution_blueprint.route('/event/<int:id>/', methods=('GET',))
def event_contributions():
    pass


@login_required
@event_contribution_blueprint.route('/event/<int:eventId>/', methods=('POST',))
def post_event_contribution(eventId):
    if request.method == 'POST':
        if not current_user.is_authenticated:
            raise InvalidUsage(message='Method Not Allowed', status_code=405)

        request_json = request.get_json()
        text = request_json.get('text', None)
        images_and_captions = request_json.get('images_and_captions', None)

        event = Event.query.get(int(eventId))

        if images_and_captions is not None:
            # check if the post request has the file part
            event_images.add_images_to_event(event, images_and_captions, text)
        else:
            # text only contribution
            add_contribution(event, text=text)

    return jsonify('Contribution uploaded'), 201


@login_required
@event_contribution_blueprint.route('/image/<int:id>', methods=('PUT',))
def voteImage(id):
    if not current_user.is_authenticated:
        raise InvalidUsage(message='Method Not Allowed', status_code=405)
    data = request.get_json()
    vote = data.get('vote', None)

    # contribution = db.session.query(EventContribution).get(contributionid)
    eventimage = EventImage.query.get(int(id))
    if not vote:
        raise InvalidAPIRequest('Vote required')

    vote_status = eventimage.vote(user_id=current_user.id, vote=vote)
    print(vote_status)
    # check if contribution has been voted by user yet or not
    return jsonify(eventimage.to_dict())


# reports

@login_required
@event_contribution_blueprint.route('/<int:id>/report/', methods=('POST',))
def event_contribution_report(id):
    contribution = EventContribution.query.get(id)
    reason_text = None
    if request.args.get('reason_text'):
        reason_text = request.args.get('reason_text')
    report = Report(
        event_contribution=contribution.id,
        creator=current_user.id,
        user=contribution.creator_id,
        reason_text=reason_text)
    db.session.add(report)
    # ADD EMAIL ACTION HERE
    db.session.commit()
    return jsonify('Contribution reported'), 201


@login_required
@event_contribution_blueprint.route(
    '/image/<int:id>/report/', methods=('POST',))
def event_image_report(id):
    event_image = EventImage.query.get(id)
    reason_text = None
    if request.args.get('reason_text'):
        reason_text = request.args.get('reason_text')
    report = Report(
        event_image=event_image.id,
        creator=current_user.id,
        user=event_image.creator_id,
        reason_text=reason_text)
    db.session.add(report)
    # ADD EMAIL ACTION HERE
    db.session.commit()
    return jsonify('Contribution reported'), 201
