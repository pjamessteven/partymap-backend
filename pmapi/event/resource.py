from sqlalchemy import or_, and_
from flask_login import current_user, login_required
from flask import Blueprint, request, jsonify

from .model import Event
from . import controllers as events
from pmapi.exceptions import InvalidUsage, InvalidAPIRequest, RecordNotFound
from pmapi.extensions import db, activity_plugin

import pmapi.activity.controllers as activities
import pmapi.event_tag.controllers as event_tags
import pmapi.event_date.controllers as event_dates
from pmapi.event_tag.model import EventTag, \
    event_tag_upvotes, event_tag_downvotes

events_blueprint = Blueprint('events', __name__)

Activity = activity_plugin.activity_cls


@events_blueprint.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@login_required
@events_blueprint.route('/owned/', methods=('GET',))
def get_following():
    all = events.get_owned_events()
    return jsonify([e.minified() for e in all])


@events_blueprint.route('/<int:id>/', methods=('GET',))
def get_event(id):
    e = events.get_event_by_id_or_404(id)

    if current_user.is_authenticated:
        return jsonify(e.to_dict(current_user))
    else:
        return jsonify(e.to_dict())


# get an events revisions
@events_blueprint.route('/<int:id>/revisions/', methods=('GET',))
def get_event_revisions(id):
    e = events.get_event_by_id_or_404(id)

    return jsonify(e.revisions())


# get an events activities
@events_blueprint.route('/<int:id>/activity/', methods=('GET',))
def get_event_activity(id):
    e = events.get_event_by_id_or_404(id)

    return jsonify(activities.get_activities_for_item(e))


@events_blueprint.route('/', methods=('GET',))
def query_events():
    if request.args.get('query'):
        query = request.args.get('query')
        results = events.search_events(query)

        if request.args.get('page'):
            page = int(request.args.get('page'))
        else:
            page = 1

        paginated = results.paginate(page, 5)

        return jsonify([e.minified() for e in paginated.items]), 200

    else:
        # raise exception
        pass


@login_required
@events_blueprint.route('/', methods=('POST',))
def addEvent():
    if request.method == 'POST':

        data = request.get_json()
        dateTime = data.get('dateTime', None)
        location = data.get('location', None)
        description = data.get('description', None)
        name = data.get('name', None)
        url = data.get('url', None)
        rrule = data.get('rrule', None)
        tags = data.get('tags', None)
        images = data.get('images_and_captions', None)

        if not name or not url or not description or not location:
            raise InvalidAPIRequest(
                message='Missing required info', status_code=405)

        event = events.add_event(name, description, url, dateTime,
                                 rrule, location, tags, images)
        return event.to_dict()


# update event by ID number
@events_blueprint.route('/<int:id>/', methods=('PUT',))
@login_required
def update_event(id):
    data = request.get_json()
    print(data)
    event = Event.query.get(id)
    rrule = data.get('rrule')
    url = data.get('url')
    location = data.get('location')
    dateTime = data.get('dateTime')
    description = data.get('description')
    tags = data.get('tags')

    if description:
        event.description = description
        activity = Activity(verb=u'update', object=event)
        # create_notification('UPDATE EVENT', activity, event.followers)
        db.session.add(activity)

    if rrule is False:
        db.session.delete(event.rrule)

    if dateTime and location and rrule:
        return event_dates.generate_future_event_dates(
            event, dateTime, location, rrule, url)

    if tags:
        event_tags.add_tags_to_event(tags, event)

    current_user.owned_events.append(event)
    db.session.commit()

    return jsonify(event.to_dict()), 201

# votes
@events_blueprint.route('/<int:event_id>/tag/<string:tag_id>/', methods=('PUT',))
@login_required
def voteTag(event_id, tag_id):
    if not current_user.is_authenticated:
        raise InvalidUsage(message='Method Not Allowed', status_code=405)

    event = Event.query.get(event_id)
    data = request.get_json()
    vote = data['vote']
    print('vote tag called')

    et = EventTag.query.filter(
        and_(
            EventTag.tag_id == tag_id,
            EventTag.event_id == event_id)
    ).one()

    if not et:
        raise RecordNotFound('Tag does not exist')

    if not vote:
        raise InvalidAPIRequest('Vote missing')

    vote_status = et.vote(user_id=current_user.id, vote=vote)

    print('current votes:')
    print(et.votes)
    # if et has negative -2 vote, delete it
    if et.votes < 0 or (et.votes == 1 and vote == -1 and vote_status == -2):
        # delete all records of upvotes/downvotes
        db.engine.execute(
            event_tag_downvotes.delete(
                db.and_(
                    event_tag_downvotes.c.tag == et.tag_id,
                    event_tag_downvotes.c.event_id == et.event_id
                )
            )
        )
        db.engine.execute(
            event_tag_upvotes.delete(
                db.and_(
                    event_tag_downvotes.c.tag == et.tag_id,
                    event_tag_downvotes.c.event_id == et.event_id
                )
            )
        )
        db.session.delete(et)
        print('deleted')

    current_user.owned_events.append(event)
    db.session.commit()
    print(vote_status)
    # check if contribution has been voted by user yet or not
    return jsonify(et.to_dict())
