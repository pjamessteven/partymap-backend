from flask_login import current_user
from pmapi.extensions import db
from .model import Tag, EventTag


def add_tags_to_event(tags, event):
    for t in tags:
        print(t)
        tag = Tag(tag=t)

        # check if tag is already in db
        if db.session.query(Tag).filter(Tag.tag == t).count():
            tag = db.session.query(Tag).filter(Tag.tag == t).one()

        # don't add duplicate event tag
        if db.session.query(EventTag).filter(
                EventTag.tag == tag, EventTag.event == event).count():
            pass
        else:
            et = EventTag(
                tag=tag,
                event=event,
                creator=current_user)
            db.session.add(et)
            db.session.commit()
            et.vote(current_user.id, 1)
