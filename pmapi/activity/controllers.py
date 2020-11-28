from pmapi.extensions import db, activity_plugin
from sqlalchemy_continuum import transaction_class
from sqlalchemy_continuum import versioning_manager
from sqlalchemy import or_
from sqlalchemy import inspect
from sqlalchemy import join
from sqlalchemy.sql import select
def get_activities_for_actor(user):
    Activity = activity_plugin.activity_cls
    Transaction = versioning_manager.transaction_cls

    mapper = inspect(Activity)

    for column in mapper.attrs:
        print(column.key)
    mapper = inspect(Transaction)

    for column in mapper.attrs:
        print(column.key)

    activities = db.session.query(Activity).join(Transaction, Activity.transaction_id == Transaction.id).filter(
            Transaction.user_id == user.id
    ).order_by(Activity.id.desc())

    print(activities.all())

    '''
    j = join(Activity, Transaction, Activity.transaction_id == Transaction.id)

    stmt = select([Activity]).where(Transaction.user_id == user.id).select_from(j)
    activities = db.engine.execute(stmt)
    print(activities)
    activities = activities.fetchall()
    print(activities)
    for row in result:
        print(row)
     '''
    return [create_activity_dict(a) for a in activities]


def get_activities_for_item(item):
    Activity = activity_plugin.activity_cls

    activities = db.session.query(Activity).filter(
        or_(
            Activity.object == item,
            Activity.target == item
        )
    ).order_by(Activity.id.desc())

    return [create_activity_dict(a) for a in activities]


def get_most_recent_activity_for_item(item):
    Activity = activity_plugin.activity_cls

    activity = db.session.query(Activity).filter(
        or_(
            Activity.object == item,
            Activity.target == item
        )
    ).order_by(Activity.id.desc()).first()

    if activity:
        return create_activity_dict(activity)
    else:
        return None


def create_activity_dict(a):
    object = None
    if (hasattr(a.object, 'to_dict')):
        object = a.object.to_dict(activity=False)
        # acivity flag is so that we don't create an infinite loop
    return {
        'actor': a.actor.username,
        'time': a.transaction.issued_at,
        'changeset': a.object_version.changeset,
        'object': object,
        'verb': a.verb,
        'type': a.object_type,
        'transaction_id': a.transaction.id,
        'id': a.id
    }
