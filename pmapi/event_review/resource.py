from flask import Blueprint
from flask_apispec import marshal_with
from flask_apispec import MethodResource
from flask_apispec import use_kwargs
from flask_apispec import doc
from marshmallow import fields
from flask_login import login_required
from . import controllers as event_reviews
from .schemas import EventReviewSchema
from . import permissions as permissions

event_review_blueprint = Blueprint("event_review", __name__)


@doc(tags=["event_reviews"])
class AddEventReviewResource(MethodResource):
    @login_required
    @doc(summary="Add a review", description="Adds a review to an event")
    @use_kwargs(
        {
            "text": fields.Str(required=False),
            "rating": fields.Integer(required=False),
            "media_items": fields.List(fields.Dict(), required=False, allow_none=True),
            "event_date_id": fields.Integer(required=False),
        }
    )
    @marshal_with(EventReviewSchema(), code=200)
    def post(self, event_id, **kwargs):
        return event_reviews.add_review(event_id, **kwargs)


event_review_blueprint.add_url_rule(
    "/event/<event_id>/",
    view_func=AddEventReviewResource.as_view(
        "AddEventReviewResource"),
)


@doc(tags=["event_reviews"])
class EventReviewResource(MethodResource):
    @permissions.delete
    @doc(summary="Delete a review", description="Deletes a review")
    def delete(self, review_id, **kwargs):
        return event_reviews.delete_review(review_id)
    
event_review_blueprint.add_url_rule(
    "/<review_id>",
    view_func=EventReviewResource.as_view("EventReviewResource"),
)

"""

@event_review_blueprint.route("/event/<int:id>/", methods=("GET",))
def event_reviews():
    pass


@login_required
@event_review_blueprint.route("/event/<int:eventId>/", methods=("POST",))
def post_event_review(eventId):
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
            # text only review
            add_review(event, text=text)

    return jsonify("review uploaded"), 201


@login_required
@event_review_blueprint.route("/image/<int:id>", methods=("PUT",))
def voteImage(id):
    if not current_user.is_authenticated:
        raise InvalidUsage(message="Method Not Allowed", status_code=405)
    data = request.get_json()
    vote = data.get("vote", None)

    # review = db.session.query(EventReview).get(reviewid)
    eventimage = EventImage.query.get(int(id))
    if not vote:
        raise InvalidAPIRequest("Vote required")

    vote_status = eventimage.vote(user_id=current_user.id, vote=vote)
    print(vote_status)
    # check if review has been voted by user yet or not
    return jsonify(eventimage.to_dict())


# reports


@login_required
@event_review_blueprint.route("/<int:id>/report/", methods=("POST",))
def event_review_report(id):
    review = EventReview.query.get(id)
    reason_text = None
    if request.args.get("reason_text"):
        reason_text = request.args.get("reason_text")
    report = Report(
        event_review=review.id,
        creator=current_user.id,
        user=review.creator_id,
        reason_text=reason_text,
    )
    db.session.add(report)
    # ADD EMAIL ACTION HERE
    db.session.commit()
    return jsonify("review reported"), 201


@login_required
@event_review_blueprint.route("/image/<int:id>/report/", methods=("POST",))
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
    return jsonify("review reported"), 201

"""
