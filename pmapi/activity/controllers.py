from pmapi.extensions import db, activity_plugin
from sqlalchemy_continuum import versioning_manager
from sqlalchemy import or_
from sqlalchemy import inspect
from pmapi.common.controllers import paginated_results
import pprint


def get_activities_for_actor(user):
    Activity = activity_plugin.activity_cls
    Transaction = versioning_manager.transaction_cls

    mapper = inspect(Activity)

    for column in mapper.attrs:
        print(column.key)
    mapper = inspect(Transaction)

    for column in mapper.attrs:
        print(column.key)

    activities = (
        db.session.query(Activity)
        .join(Transaction, Activity.transaction_id == Transaction.id)
        .filter(Transaction.user_id == user.id)
        .order_by(Activity.id.desc())
    )

    """
    j = join(Activity, Transaction, Activity.transaction_id == Transaction.id)

    stmt = select([Activity]).where(Transaction.user_id == user.id).select_from(j)
    activities = db.engine.execute(stmt)
    print(activities)
    activities = activities.fetchall()
    print(activities)
    for row in result:
        print(row)
     """
    return activities


def get_activities_associated_with_target_transaction(transaction_id, **kwargs):
    Activity = activity_plugin.activity_cls

    query = (
        db.session.query(Activity)
        .filter(Activity.target_tx_id == transaction_id)
        .order_by(Activity.id.desc())
    )
    return paginated_results(Activity, query=query, **kwargs)


def get_activities_for_item(**kwargs):
    Activity = activity_plugin.activity_cls
    item = kwargs.pop("item")
    query = (
        db.session.query(Activity)
        .filter(or_(Activity.object == item, Activity.target == item))
        .order_by(Activity.id.desc())
    )

    return paginated_results(Activity, query=query, **kwargs)


def get_most_recent_activity_for_item(item):
    Activity = activity_plugin.activity_cls

    activity = (
        db.session.query(Activity)
        .filter(or_(Activity.object == item, Activity.target == item))
        .order_by(Activity.id.desc())
        .one()
    )

    return activity
