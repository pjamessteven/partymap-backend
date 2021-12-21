from pmapi.extensions import db, activity_plugin
from pmapi.common.controllers import paginated_results
from sqlalchemy import or_, and_

from .model import Tag, EventTag
from pmapi.event_date.model import EventDate
from pmapi.event.model import Event

Activity = activity_plugin.activity_cls


def add_tags_to_event(tags, event):
    for t in tags:
        tag = Tag(tag=t)

        # check if tag is already in db
        if db.session.query(Tag).filter(Tag.tag == t).count():
            tag = db.session.query(Tag).filter(Tag.tag == t).one()

        # remove tag if it already exists
        if (
            db.session.query(EventTag)
            .filter(EventTag.tag == tag, EventTag.event == event)
            .count()
        ):
            et = (
                db.session.query(EventTag)
                .filter(EventTag.tag == tag, EventTag.event == event)
                .one()
            )
            db.session.delete(et)
            # raise exc.RecordAlreadyExists("Tag already exists for event")
            # delete activity
            db.session.flush()
            activity = Activity(verb=u"delete", object=et, target=event)
            db.session.add(activity)

        else:
            et = EventTag(tag=tag, event=event)
            db.session.add(et)
            # add activity
            db.session.flush()
            activity = Activity(verb=u"create", object=et, target=event)
            db.session.add(activity)

    db.session.commit()
    return tags


def get_tags(**kwargs):
    query = db.session.query(Tag)

    if "date_min" in kwargs:
        query = query.join(EventTag).join(Event).join(EventDate)
        query = query.filter(EventDate.start_naive >= kwargs.pop("date_min"))
    if "date_max" in kwargs:
        date_max = kwargs.pop("date_max")
        query = query.filter(
            and_(
                or_(
                    EventDate.end_naive <= date_max,
                    EventDate.end_naive.is_(None),
                ),
                EventDate.start_naive <= date_max,
            )
        )

    if kwargs.get("tag_name", None) is not None:
        tag_name = kwargs.pop("tag_name")
        if len(tag_name) > 0:
            query_string = ""
            for word in tag_name.split():
                # formulate a query string like 'twisted:* frequncey:*'
                if word == tag_name.split()[-1]:
                    query_string = query_string + (word + str(":*"))
                else:
                    query_string = query_string + (word + str(" & "))

            query = query.filter(
                Tag.__ts_vector__.match(query_string, postgresql_regconfig="english")
            )

    return paginated_results(Tag, query.distinct(), **kwargs)
