from flask import Blueprint, jsonify
from flask_apispec import doc
from flask_apispec import marshal_with
from flask_apispec import MethodResource
from flask_apispec import use_kwargs
from flask_login import login_required
from flask_login import current_user
from pmapi.common.controllers import paginated_view_args
from pmapi.event.model import Event
from pmapi.extensions import db, activity_plugin
from pmapi.activity.schemas import ActivityListSchema

from sqlalchemy.orm import make_transient
from . import controllers as activities

Activity = activity_plugin.activity_cls

activity_blueprint = Blueprint("activity", __name__)

"""
@doc(tags=["events", "activity"])
class RevertActivityResource(MethodResource):
    @doc(summary="Revert activity", description="Revert activity")
    @use_kwargs(
        {
            **paginated_view_args(sort_options=[]),
        },
        location="query",
    )
    @marshal_with(ActivityListSchema(), code=200)
    def get(self, activity_id, **kwargs):
        event = events.get_event_or_404(event_id)
        return activities.get_activities_for_item(**kwargs, item=event)


activity_blueprint.add_url_rule(
    "/<activity_id>/revert/",
    view_func=RevertActivityResource.as_view("RevertActivityResource"),
)
"""


@doc(tags=["events", "activity"])
class ActivitiesOfTransactionResource(MethodResource):
    @doc(
        summary="Activities of transaction",
        description="Get all activities associated with a given transaction",
    )
    @use_kwargs(
        {
            **paginated_view_args(sort_options=[]),
        },
        location="query"
    )
    @marshal_with(ActivityListSchema(), code=200)
    def get(self, transaction_id, **kwargs):
        return activities.get_activities_associated_with_target_transaction(
            transaction_id, **kwargs
        )


activity_blueprint.add_url_rule(
    "/transaction/<transaction_id>/",
    view_func=ActivitiesOfTransactionResource.as_view(
        "ActivitiesOfTransactionResource"
    ),
)

"""
@activity_blueprint.route("/<int:id>/revert/", methods=("GET",))
def revert(id):
    # THIS IS ALL FUCKED (well, only kinda. i'll deal with it later)
    # need to think about a good way to let users undo a recent change
    # without destroying everything
    activity = Activity.query.get(id)

    previous_target_version = activity.target_version.previous

    target_version_tx_id = activity.target_version.transaction_id
    previous_target_version_tx_id = None

    if hasattr(previous_target_version, "transaction_id"):
        previous_target_version_tx_id = previous_target_version.transaction_id

    db.session.expunge(activity)
    # target version should always be an event

    for obj in db.session:
        print(obj)

    relations_list = []

    if previous_target_version.event_tags is not None:
        relations_list.append("event_tags")
    if previous_target_version.event_dates is not None:
        relations_list.append("event_dates")

    previous_target_version = previous_target_version.revert(relations_list)

    # release activity from db session so that the object_version (object_tx_id) is not updated
    # in this transaction
    db.session.flush()

    new_activity = Activity(
        verb=u"revert",
        data={
            "previous_target_version_tx_id": previous_target_version_tx_id,
            "target_version_tx_id": target_version_tx_id,
        },
        object=previous_target_version,
        target=previous_target_version,
    )  # might need to add event as target if eventdate etc.

    db.session.add(new_activity)
    db.session.flush()

    db.session.commit()

    return jsonify({"ok": True}), 201



"""
