from flask_login import current_user

from sqlalchemy import delete
from sqlalchemy_continuum import version_class
from .model import EventReview, event_review_downvotes, event_review_upvotes
from pmapi.extensions import db, activity_plugin
import pmapi.event.controllers as events
import pmapi.event_date.controllers as event_dates
import pmapi.media_item.controllers as media_items
import pmapi.activity.controllers as activities
import pmapi.exceptions as exc
from pmapi.common.controllers import paginated_results

from sqlalchemy.orm import joinedload

Activity = activity_plugin.activity_cls

def get_review(id):
    return EventReview.query.get(id)

def get_review_or_404(id):
    review = get_review(id)
    if not review:
        msg = "No such review with id {}".format(id)
        raise exc.RecordNotFound(msg)
    return review

# return top level posts for an event and their direct children
def get_event_reviews(event_id, **kwargs):
    event = events.get_event_or_404(event_id)
    
    query = db.session.query(EventReview).options(
        joinedload(EventReview.children)
    ).filter(
        EventReview.event_id == event.id,
        EventReview.parent_id.is_(None)
    ).order_by(
        EventReview.created_at.desc() # Sort parent reviews by created_at DESC
    )

    return paginated_results(EventReview, query, **kwargs)

def get_event_review_and_children(event_review_id):
    review = get_review_or_404(event_review_id)

    return db.session.query(EventReview).options(
        joinedload(EventReview.children)
    ).filter(
        EventReview.id == review.id
    ).first()

def delete_review(id):
    review = get_review_or_404(id)

    for media_item in review.media_items:
        media_items.delete_item(media_item)

    # delete votes
    delete_upvotes = delete(event_review_upvotes).where(event_review_upvotes.c.event_review_id == review.id)
    delete_downvotes = delete(event_review_downvotes).where(event_review_downvotes.c.event_review_id == review.id)
    db.session.execute(delete_upvotes)
    db.session.execute(delete_downvotes)
    
    db.session.flush()
    db.session.delete(review)
    db.session.flush()

    # Hard delete... this review never existed...
    EventReviewVersion = version_class(EventReview)
    db.session.query(EventReviewVersion).filter_by(id=review.id).delete()
    activities.delete_activities_for_item(review)
    
    db.session.commit()

def add_review(event_id, creator=current_user, **kwargs):
    text = kwargs.pop("text", None)
    media = kwargs.pop("media_items", None)
    event_date_id = kwargs.pop("event_date_id", None)

    parent_id = kwargs.pop("parent_id", None)

    event = events.get_event_or_404(event_id)

    event_date = None

    if event_date_id:
        event_date = event_dates.get_event_date_or_404(event_date_id)

    # add images to event_date album
    items = []
    if media:
        items = media_items.add_media_to_event(
            media, event, event_date, creator)

    review = EventReview(
        media_items=items,
        text=text,
        event_date_id=event_date_id,
        event_id=event_id,
        creator_id=creator.get_id(),
        parent_id=parent_id
    )



    db.session.add(review)
    
    db.session.flush()
    # add activity
    activity = Activity(verb=u"create", object=review, target=event)
    db.session.add(activity)

    db.session.commit()
    review_id = review.id
    from pmapi.celery_tasks import update_review_translation
    update_review_translation.delay(review_id)

    return review
