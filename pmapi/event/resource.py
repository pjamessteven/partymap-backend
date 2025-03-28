from flask import Blueprint, jsonify
from marshmallow import fields
from flask_apispec import doc
from flask_apispec import marshal_with
from flask_apispec import MethodResource
from flask_apispec import use_kwargs
from flask_login import login_required
from flask_login import current_user
from pmapi.hcaptcha.controllers import validate_hcaptcha
from pmapi.suggestions.controllers import add_suggested_edit
from pmapi.user.controllers import get_user_or_404
from . import controllers as events
import pmapi.activity.controllers as activities
from . import permissions as event_permissions

from pmapi.exceptions import InvalidUsage
from pmapi.common.controllers import paginated_view_args

from .schemas import (
    EventSchema,
    EventListSchema,
    EventVersionListSchema,
    ContributorListSchema,
)
from pmapi.user.schemas import UserListSchema
from pmapi.activity.schemas import ActivityListSchema

events_blueprint = Blueprint("events", __name__)

# Activity = activity_plugin.activity_cls


@doc(tags=["events"])
class EventsResource(MethodResource):
    @doc(
        summary="Get a list of events that are in the db.",
        description="""Returns a list of event dates that are in the db. \n
        ### Usage:  \n
        Start and end date format must be in ISO-8601 format.
        eg: 2020-05-23T05:00:00",
        """,
    )
    @use_kwargs(
        {
            "query": fields.String(required=False),
            "created_by": fields.String(required=False),
            "hidden": fields.Boolean(required=False),
            **paginated_view_args(sort_options=["created_at", "name", "id"]),
        },
        location="query"
    )
    @marshal_with(EventListSchema(), code=200)
    def get(self, **kwargs):
        created_by_user = None
        if "created_by" in kwargs:
            created_by_user = get_user_or_404(kwargs.pop("created_by"))
            
        return events.search_events(created_by_user, **kwargs)

    @doc(summary="Add an event", description="Add an event")
    @event_permissions.add
    @use_kwargs(
        {
            "date_time": fields.Dict(required=True),
            "location": fields.Dict(required=True),
            "description": fields.String(required=True),
            "description_attribute": fields.String(required=False, allow_none=True),
            "full_description": fields.String(required=False, allow_none=True),
            "full_description_attribute": fields.String(required=False, allow_none=True),
            "youtube_url": fields.String(required=False, allow_none=True),
            "next_event_date_description": fields.String(
                required=False, allow_none=True
            ),
            "next_event_date_description_attribute": fields.String(
                required=False, allow_none=True
            ),
            "next_event_date_size": fields.String(required=False, allow_none=True),
            "next_event_date_artists": fields.List(
                fields.Dict(), required=False, allow_none=True
            ),
            "next_event_date_lineup_images": fields.Nested(
                "MediaItemUploadSchema", many=True, allow_none=True
            ),
            "name": fields.String(required=True),
            "url": fields.String(required=False, allow_none=True),
            "tags": fields.List(fields.String(), required=False, allow_none=True),
            "media_items": fields.Nested(
                "MediaItemUploadSchema", many=True
            ),
            "logo": fields.Nested(
                "MediaItemUploadSchema", many=False
            ),
            "rrule": fields.Dict(),
            "host": fields.Boolean(),
            "tickets": fields.List(fields.Dict(), required=False, allow_none=True),
            "ticket_url": fields.String(required=False, allow_none=True),
        },
    )
    @marshal_with(EventSchema(), code=200)
    def post(self, **kwargs):
        return events.add_event(**kwargs, creator=current_user)


events_blueprint.add_url_rule(
    "/", view_func=EventsResource.as_view("EventsResource"))


@doc(tags=["events"])
class EventResource(MethodResource):
    @doc(summary="Get an event", description="Get an event")
    @marshal_with(EventSchema(), code=200)
    def get(self, event_id, **kwargs):
        return events.get_event_or_404(event_id)

    @doc(summary="Update an event", description="Update an event")
    @event_permissions.update
    @login_required
    @use_kwargs(
        {
            "date_time": fields.Dict(required=False, allow_none=True),
            "location": fields.Dict(required=False, allow_none=True),
            "description": fields.String(required=False, allow_none=True),
            "description_attribute": fields.String(required=False, allow_none=True),
            "full_description": fields.String(required=False, allow_none=True),
            "full_description_attribute": fields.String(required=False, allow_none=True),
            "youtube_url": fields.String(required=False, allow_none=True),
            "url": fields.String(required=False, allow_none=True),
            "add_tags": fields.List(fields.String(), required=False, allow_none=True),
            "remove_tags": fields.List(
                fields.String(), required=False, allow_none=True
            ),
            "hidden": fields.Boolean(required=False),
            "rrule": fields.Dict(required=False, allow_none=True),
            "remove_rrule": fields.Boolean(required=False, allow_none=True),
            "media_items": fields.List(fields.Dict(), required=False, allow_none=True),
            "logo": fields.Dict(required=False, allow_none=True),
        },
    )
    @marshal_with(EventSchema(), code=200)
    def put(self, event_id, **kwargs):
        return events.update_event(event_id, **kwargs)

    @doc(summary="Delete an event", description="Delete an event")
    @login_required
    @event_permissions.delete
    def delete(self, event_id):
        events.delete_event(event_id)
        return "", 204


events_blueprint.add_url_rule(
    "/<event_id>", view_func=EventResource.as_view("EventResource")
)


@doc(tags=["events", "suggest_edit"])
class EventSuggestEditResource(MethodResource):
    @doc(
        summary="Suggest deleting an event.",
        params={"event_id": {"description": "event ID"}},
    )
    @use_kwargs(
        {
            "message": fields.Str(required=False, allow_none=True),
            "hcaptcha_token": fields.Str(required=False, allow_none=True),
        }
    )
    def delete(self, event_id, **kwargs):
        token = kwargs.pop("hcaptcha_token", None)
        event = events.get_event_or_404(event_id)
        if not current_user.is_authenticated:
            validate_hcaptcha(token)
        return add_suggested_edit(
            event=event, action="delete", object_type="Event", **kwargs
        )

    @doc(summary="Suggest an edit to an event")
    @use_kwargs(
        {
            "date_time": fields.Dict(required=False, allow_none=True),
            "location": fields.Dict(required=False, allow_none=True),
            "description": fields.String(required=False, allow_none=True),
            "description_attribute": fields.String(required=False, allow_none=True),
            "full_description": fields.String(required=False, allow_none=True),
            "full_description_attribute": fields.String(required=False, allow_none=True),
            "youtube_url": fields.String(required=False, allow_none=True),
            "name": fields.String(required=False, allow_none=True),
            "url": fields.String(required=False, allow_none=True),
            "add_tags": fields.List(fields.String(), required=False, allow_none=True),
            "remove_tags": fields.List(
                fields.String(), required=False, allow_none=True
            ),
            "rrule": fields.Dict(required=False, allow_none=True),
            "remove_rrule": fields.Boolean(required=False, allow_none=True),
            "media_items": fields.List(fields.Dict(), required=False, allow_none=True),
            "message": fields.Str(required=False, allow_none=True),
            "hcaptcha_token": fields.Str(required=False, allow_none=True),
            "logo": fields.Dict(required=False, allow_none=True),
        },
    )
    def put(self, event_id, **kwargs):
        # used by unpriviliged users to suggest updates to an event
        token = kwargs.pop("hcaptcha_token", None)
        event = events.get_event_or_404(event_id)
        if not current_user.is_authenticated:
            validate_hcaptcha(token)

        return add_suggested_edit(
            event=event,
            action="update",
            creator_id=current_user.get_id(),
            object_type="Event",
            **kwargs
        )



events_blueprint.add_url_rule(
    "/<event_id>/suggest",
    view_func=EventSuggestEditResource.as_view("EventSuggestEditResource"),
)


@doc(tags=["events", "activity"])
class EventActivityResource(MethodResource):
    @doc(summary="Get activity for an event", description="Get activity for event")
    @use_kwargs(
        {
            **paginated_view_args(sort_options=[]),
        },
        location="query"
    )
    @marshal_with(ActivityListSchema(), code=200)
    def get(self, event_id, **kwargs):
        event = events.get_event_or_404(event_id)
        return activities.get_activities_for_item(**kwargs, item=event)


events_blueprint.add_url_rule(
    "/<event_id>/activity",
    view_func=EventActivityResource.as_view("EventActivityResource"),
)


@doc(tags=["events", "activity"])
class EventVersionsResource(MethodResource):
    @doc(summary="Get versions for an event", description="Get versions for event")
    @use_kwargs(
        {
            **paginated_view_args(sort_options=[]),
        },
        location="query"
    )
    @marshal_with(EventVersionListSchema(), code=200)
    def get(self, event_id, **kwargs):
        return events.get_event_versions(event_id, **kwargs)


events_blueprint.add_url_rule(
    "/<event_id>/versions",
    view_func=EventVersionsResource.as_view("EventVersionsResource"),
)


@doc(tags=["events", "activity"])
class EventContributorsResource(MethodResource):
    @doc(
        summary="Get contributors for an event",
        description="Get a list of users who have contributed to an event",
    )
    @use_kwargs(
        {
            **paginated_view_args(sort_options=[]),
        },
        location="query"
    )
    @marshal_with(ContributorListSchema(), code=200)
    def get(self, event_id, **kwargs):
        return events.get_event_contributors(event_id, **kwargs)


events_blueprint.add_url_rule(
    "/<event_id>/contributors",
    view_func=EventContributorsResource.as_view("EventContributorsResource"),
)


@doc(tags=["events", "favorite"])
class EventFavoriteResource(MethodResource):
    @doc(
        summary="Favorite this event",
        description="Favorite this event",
    )
    @login_required
    @use_kwargs(
        {
            "favorited": fields.Boolean(required=True),
        },
    )
    @marshal_with(EventSchema(), code=200)
    def put(self, event_id, **kwargs):
        return events.favorite_event(event_id, **kwargs)


events_blueprint.add_url_rule(
    "/<event_id>/favorite",
    view_func=EventFavoriteResource.as_view("EventFavoriteResource"),
)

"""

@login_required
@events_blueprint.route("/owned/", methods=("GET",))
def get_following():
    all = events.get_owned_events()
    return jsonify([e.minified() for e in all])


@events_blueprint.route("/<string:id>/", methods=("GET",))
def get_event(id):
    e = events.get_event_or_404(id)
    if current_user.is_authenticated:
        return jsonify(e.to_dict(current_user))
    else:
        return jsonify(e.to_dict())


# get an events revisions
@events_blueprint.route("/<int:id>/revisions/", methods=("GET",))
def get_event_revisions(id):
    e = events.get_event_or_404(id)

    return jsonify(e.revisions())


# get an events activities
@events_blueprint.route("/<int:id>/activity/", methods=("GET",))
def get_event_activity(id):
    e = events.get_event_or_404(id)

    return jsonify(activities.get_activities_for_item(e))


@events_blueprint.route("/", methods=("GET",))
def query_events():
    if request.args.get("query"):
        query = request.args.get("query")
        results = events.search_events(query)

        if request.args.get("page"):
            page = int(request.args.get("page"))
        else:
            page = 1

        paginated = results.paginate(page, 5)

        return jsonify([e.minified() for e in paginated.items]), 200

    else:
        # raise exception
        pass


@login_required
@events_blueprint.route("/", methods=("POST",))
def addEvent():
    if request.method == "POST":

        data = request.get_json()
        dateTime = data.get("dateTime", None)
        location = data.get("location", None)
        description = data.get("description", None)
        name = data.get("name", None)
        url = data.get("url", None)
        rrule = data.get("rrule", None)
        tags = data.get("tags", None)
        images = data.get("images_and_captions", None)

        if not name or not url or not description or not location:
            raise InvalidAPIRequest(message="Missing required info", status_code=405)

        event = events.add_event(
            name, description, url, dateTime, rrule, location, tags, images
        )
        return event.to_dict()


# update event by ID number
@login_required
@events_blueprint.route("/<string:id>/", methods=("PUT",))
def update_event(id):
    print("update event", id)
    data = request.get_json()
    print(data)
    event = Event.query.get(id)
    rrule = data.get("rrule")
    url = data.get("url")
    location = data.get("location")
    dateTime = data.get("dateTime")
    description = data.get("description")
    tags = data.get("tags")

    if description:
        event.description = description
        activity = Activity(verb=u"update", object=event)
        # create_notification('UPDATE EVENT', activity, event.followers)
        db.session.add(activity)

    if rrule is False:
        db.session.delete(event.rrule)

    if dateTime and location and rrule:
        return event_dates.generate_future_event_dates(
            event, dateTime, location, rrule, url
        )

    if tags:
        event_tags.add_tags_to_event(tags, event)

    db.session.commit()

    return jsonify(event.to_dict()), 201


# votes
@events_blueprint.route("/<int:event_id>/tag/<string:tag_id>/", methods=("PUT",))
@login_required
def voteTag(event_id, tag_id):
    if not current_user.is_authenticated:
        raise InvalidUsage(message="Method Not Allowed", status_code=405)

    event = Event.query.get(event_id)
    data = request.get_json()
    vote = data["vote"]
    print("vote tag called")

    et = EventTag.query.filter(
        and_(EventTag.tag_id == tag_id, EventTag.event_id == event_id)
    ).one()

    if not et:
        raise RecordNotFound("Tag does not exist")

    if not vote:
        raise InvalidAPIRequest("Vote missing")

    vote_status = et.vote(user_id=current_user.id, vote=vote)

    print("current votes:")
    print(et.votes)
    # if et has negative -2 vote, delete it
    if et.votes < 0 or (et.votes == 1 and vote == -1 and vote_status == -2):
        # delete all records of upvotes/downvotes
        db.engine.execute(
            event_tag_downvotes.delete(
                db.and_(
                    event_tag_downvotes.c.tag == et.tag_id,
                    event_tag_downvotes.c.event_id == et.event_id,
                )
            )
        )
        db.engine.execute(
            event_tag_upvotes.delete(
                db.and_(
                    event_tag_downvotes.c.tag == et.tag_id,
                    event_tag_downvotes.c.event_id == et.event_id,
                )
            )
        )
        db.session.delete(et)
        print("deleted")

    current_user.owned_events.append(event)
    db.session.commit()
    print(vote_status)
    # check if review has been voted by user yet or not
    return jsonify(et.to_dict())
"""
