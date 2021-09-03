from flask_login import current_user
from pmapi.extensions import db
from pmapi.common.controllers import paginated_results
import pmapi.exceptions as exc
from sqlalchemy import or_, and_

from .model import Tag, EventTag
from pmapi.event_date.model import EventDate
from pmapi.event.model import Event


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
            tag = (
                db.session.query(EventTag)
                .filter(EventTag.tag == tag, EventTag.event == event)
                .one()
            )
            db.session.delete(tag)
            # raise exc.RecordAlreadyExists("Tag already exists for event")

        else:
            et = EventTag(tag=tag, event=event)
            db.session.add(et)
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

    if "tag_name" in kwargs:
        tag_name = kwargs.pop("tag_name")
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
    print(query.all())
    return paginated_results(Tag, query.distinct(), **kwargs)
