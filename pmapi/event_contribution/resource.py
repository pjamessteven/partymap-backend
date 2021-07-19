from flask import Blueprint
from flask_apispec import marshal_with
from flask_apispec import MethodResource
from flask_apispec import use_kwargs
from flask_apispec import doc
from marshmallow import fields

from . import controllers as event_contributions
from .schemas import EventContributionSchema

event_contribution_blueprint = Blueprint("event_contribution", __name__)


@doc(tags=["event_contributions"])
class AddEventContributionResource(MethodResource):
    @doc(summary="Add a contribution", description="Adds a contribution to an event")
    @use_kwargs(
        {
            "text": fields.Str(required=False),
            "media_items": fields.List(fields.Dict(), required=False, allow_none=True),
            "event_date_id": fields.UUID(required=False),
        }
    )
    @marshal_with(EventContributionSchema(), code=200)
    def post(self, event_id, **kwargs):
        return event_contributions.add_contribution(event_id, **kwargs)


event_contribution_blueprint.add_url_rule(
    "/<event_id>",
    view_func=AddEventContributionResource.as_view("AddEventContributionResource"),
)


@doc(tags=["event_contributions"])
class EventContributionResource(MethodResource):
    @doc(summary="Delete a contribution", description="Deletes a contribution")
    def delete(self, contribution_id, **kwargs):
        return event_contributions.delete_contribution(**kwargs)


event_contribution_blueprint.add_url_rule(
    "/id/<contribution_id>",
    view_func=EventContributionResource.as_view("EventContributionResource"),
)

"""

@event_contribution_blueprint.route("/event/<int:id>/", methods=("GET",))
def event_contributions():
    pass


@login_required
@event_contribution_blueprint.route("/event/<int:eventId>/", methods=("POST",))
def post_event_contribution(eventId):
    if request.method == "POST":
        if not current_user.is_authenticated:
            raise InvalidUsage(message="Method Not Allowed", status_code=405)

        request_json = request.get_json()
        text = request_json.get("text", None)
        images_and_captions = request_json.get("images_and_captions", None)

        event = Event.query.get(int(eventId))

        if images_and_captions is not None:
            # check if the post request has the file part
            event_images.add_images_to_event(event, images_and_captions, text)
        else:
            # text only contribution
            add_contribution(event, text=text)

    return jsonify("Contribution uploaded"), 201


@login_required
@event_contribution_blueprint.route("/image/<int:id>", methods=("PUT",))
def voteImage(id):
    if not current_user.is_authenticated:
        raise InvalidUsage(message="Method Not Allowed", status_code=405)
    data = request.get_json()
    vote = data.get("vote", None)

    # contribution = db.session.query(EventContribution).get(contributionid)
    eventimage = EventImage.query.get(int(id))
    if not vote:
        raise InvalidAPIRequest("Vote required")

    vote_status = eventimage.vote(user_id=current_user.id, vote=vote)
    print(vote_status)
    # check if contribution has been voted by user yet or not
    return jsonify(eventimage.to_dict())


# reports


@login_required
@event_contribution_blueprint.route("/<int:id>/report/", methods=("POST",))
def event_contribution_report(id):
    contribution = EventContribution.query.get(id)
    reason_text = None
    if request.args.get("reason_text"):
        reason_text = request.args.get("reason_text")
    report = Report(
        event_contribution=contribution.id,
        creator=current_user.id,
        user=contribution.creator_id,
        reason_text=reason_text,
    )
    db.session.add(report)
    # ADD EMAIL ACTION HERE
    db.session.commit()
    return jsonify("Contribution reported"), 201


@login_required
@event_contribution_blueprint.route("/image/<int:id>/report/", methods=("POST",))
def event_image_report(id):
    event_image = EventImage.query.get(id)
    reason_text = None
    if request.args.get("reason_text"):
        reason_text = request.args.get("reason_text")
    report = Report(
        event_image=event_image.id,
        creator=current_user.id,
        user=event_image.creator_id,
        reason_text=reason_text,
    )
    db.session.add(report)
    # ADD EMAIL ACTION HERE
    db.session.commit()
    return jsonify("Contribution reported"), 201

"""
