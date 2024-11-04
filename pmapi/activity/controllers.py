
from pmapi.event.model import Event
from pmapi.event_date.model import EventDate
from pmapi.extensions import db, activity_plugin
from pmapi.user.model import User
from sqlalchemy_continuum import versioning_manager, version_class
from sqlalchemy import or_, desc, and_
from sqlalchemy import inspect
from sqlalchemy.orm import contains_eager, aliased
from collections import defaultdict
from pmapi.common.controllers import CustomPagination, paginate_json, paginated_results
import pprint
from pmapi.exceptions import InvalidAPIRequest

from sqlalchemy.orm import joinedload
from sqlalchemy import desc, func

Activity = activity_plugin.activity_cls

def get_activities(user_id=None, **kwargs):
    Transaction = versioning_manager.transaction_cls

    # Step 1: Create a base query to join Transaction and User tables
    transactions_query = db.session.query(
        Transaction.id.label('transaction_id'),
        Transaction.issued_at,
        User.username
    ).join(
        User, User.id == Transaction.user_id  # Assuming Transaction.user_id is the foreign key to User
    ).join(
        Activity, Activity.transaction_id == Transaction.id
    ).distinct(
        Transaction.id
    )    # only return transactions that have activities

    # Apply user_id filter if provided
    if user_id:
        transactions_query = transactions_query.filter(Transaction.user_id == user_id)


    transactions_query = transactions_query.filter(
        or_(
            and_(
                or_(Activity.verb == 'create', Activity.verb == 'update'),
                Activity.target_type == 'Event'
            ),
            and_(
                or_(Activity.verb == 'create', Activity.verb == 'update'),
                Activity.object_type == 'EventReview'
            )
        )
    )
    
    transactions_query = transactions_query.order_by(desc(Transaction.id))

    # Manual pagination
    page = kwargs.get('page', 1)
    per_page = kwargs.get('per_page', 10)
    total = transactions_query.count()

    if page > 0:
        transactions_query = transactions_query.offset((page - 1) * per_page).limit(per_page)


    transactions = transactions_query.all()

    # Fetch all activity details for the transaction ids
    transaction_ids = [transaction.transaction_id for transaction in transactions]
    activities_query = db.session.query(Activity).filter(Activity.transaction_id.in_(transaction_ids)).order_by(desc(Activity.id))
    activities = activities_query.all()

    # Group activities by transaction_id
    activities_by_transaction = defaultdict(list)
    for activity in activities:
        activities_by_transaction[activity.transaction_id].append(activity)

    # Step 2: Organize results into desired JSON format
    json_result = []
    for transaction in transactions:
        activities = activities_by_transaction[transaction.transaction_id]
        json_result.append({
            "transaction_id": transaction.transaction_id,
            "issued_at": transaction.issued_at,
            "username": transaction.username,
            "activities": activities,
        })
    return CustomPagination(json_result, page, per_page, total)

def get_activities_unique(user_id=None, **kwargs):
    query = db.session.query(Activity)
    if user_id:
        Transaction = versioning_manager.transaction_cls
        user_transactions = db.session.query(Transaction).filter_by(user_id=user_id).all()
        transaction_ids = [transaction.id for transaction in user_transactions]

        query = query.filter(Activity.transaction_id.in_(transaction_ids))

    return paginated_results(Activity, query, **kwargs)



def get_activities_associated_with_target_transaction(transaction_id, **kwargs):
    query = (
        db.session.query(Activity)
        .filter(Activity.target_tx_id == transaction_id)
        .order_by(Activity.id.desc())
    )
    return paginated_results(Activity, query=query, **kwargs)


def get_activities_for_item(**kwargs):
    item = kwargs.pop("item")
    query = (
        db.session.query(Activity)
        .filter(or_(Activity.object == item, Activity.target == item))
        .order_by(Activity.id.desc())
    )

    return paginated_results(Activity, query=query, **kwargs)


def get_most_recent_activity_for_item(item):
    activity = (
        db.session.query(Activity)
        .filter(or_(Activity.object == item, Activity.target == item))
        .order_by(Activity.id.desc())
        .one()
    )

    return activity

def delete_activities_for_item(item):
    activities = db.session.query(Activity).filter(Activity.object == item).all()
    for activity in activities:
        db.session.delete(activity)
    return
