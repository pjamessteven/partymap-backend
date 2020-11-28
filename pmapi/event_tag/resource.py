from flask import Blueprint, Response, request, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required

from pmapi.user.model import User
from pmapi.event_tag.model import EventTag, Tag

event_tags_blueprint = Blueprint('attributes', __name__)


@event_tags_blueprint.route('/', methods=('GET',))
def query_attributes():
    if request.method == 'GET':
        if request.args.get('query'):

            query = request.args.get('query')
            query_text = ''

            for word in query.split():
                # this is to formulate a query string like 'twisted:* frequncey:*'
                if word == query.split()[-1]:
                    query_text = query_text + (word+str(':*'))
                else:
                    query_text = query_text + (word+str(' & '))

            tags = Tag.query.filter(Tag.__ts_vector__.match(query_text, postgresql_regconfig='english'))
            artists = Artist.query.filter(Artist.__ts_vector__.match(query_text, postgresql_regconfig='english'))
            print(query_text)
            if request.args.get('page'):
                page = int(request.args.get('page'))
            else:
                page = 1

            # paginate
            #results = results.order_by(EventDate.event_start.asc())

            paginated = tags.paginate(page, 10).items + artists.paginate(page, 10).items
            print(paginated)
            return jsonify([a.to_dict_count() for a in paginated]), 200

        else:
            # return all attributes
            attrs = Tag.query.all() + Artist.query.all()
            attrsdict = [t.to_dict() for t in attrs]
            return jsonify (attrsdict), 201
    else:
        return jsonify ('Invalid usage'), 401

@event_tags_blueprint.route('/tags/', methods=('GET',))
def query_tags():
    if request.method == 'GET':
        if request.args.get('query'):

            query = request.args.get('query')
            query_text = ''
            print(query)
            for word in query.split():
                # this is to formulate a query string like 'twisted:* frequncey:*'
                if word == query.split()[-1]:
                    query_text = query_text + (word+str(':*'))
                else:
                    query_text = query_text + (word+str(' & '))

            tags = Tag.query.filter(Tag.__ts_vector__.match(query_text, postgresql_regconfig='english'))
            if request.args.get('page'):
                page = int(request.args.get('page'))
            else:
                page = 1

            # paginate
            #results = results.order_by(EventDate.event_start.asc())

            paginated = tags.paginate(page, 10).items
            print(paginated)
            return jsonify([a.to_dict_count() for a in paginated]), 200

        else:
            # return all attributes
            attrs = Tag.query.all()
            attrsdict = [t.to_dict() for t in attrs]
            return jsonify (attrsdict), 201
    else:
        return jsonify ('Invalid usage'), 401
