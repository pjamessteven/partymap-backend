from flask_login import current_user
from pmapi.extensions import db
from pmapi.common.controllers import paginated_results
import pmapi.exceptions as exc

from .model import Tag, EventTag


def add_tags_to_event(tags, event, user=current_user):
    for t in tags:
        tag = Tag(tag=t)

        # check if tag is already in db
        if db.session.query(Tag).filter(Tag.tag == t).count():
            tag = db.session.query(Tag).filter(Tag.tag == t).one()

        # don't add duplicate event tag
        if (
            db.session.query(EventTag)
            .filter(EventTag.tag == tag, EventTag.event == event)
            .count()
        ):
            raise exc.RecordAlreadyExists("Tag already exists for event")

        else:
            et = EventTag(tag=tag, event=event, creator_id=user.id)
            db.session.add(et)
    db.session.commit()
    return tags


def get_tags(**kwargs):
    query = Tag.query
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
    return paginated_results(Tag, query, **kwargs)
