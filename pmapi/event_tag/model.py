from datetime import datetime
from sqlalchemy import Index, func, cast, select
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.hybrid import hybrid_property


from pmapi.extensions import db


def create_tsvector(*args):
    exp = args[0]
    for e in args[1:]:
        exp += " " + e
    return func.to_tsvector("english", exp)


class Tag(db.Model):
    __tablename__ = "tags"

    tag = db.Column(db.String(50), primary_key=True, nullable=False)
    events_with_tag = db.relationship("EventTag", back_populates="tag")
    artists_with_tag = db.relationship("ArtistTag", back_populates="tag")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __ts_vector__ = create_tsvector(cast(func.coalesce(tag, ""), postgresql.TEXT))

    # this is an index for searching tags
    __table_args__ = (Index("idx_events_fts", __ts_vector__, postgresql_using="gin"),)

    @hybrid_property
    def count(self):
        return len(self.events_with_tag)

    @count.expression
    def count(cls):
        return (
            select([func.count(EventTag.tag_id)])
            .where(EventTag.tag_id == cls.tag)
            .correlate(Tag)
            .label("count")
        )


class EventTag(db.Model):
    __tablename__ = "event_tags"
    __versioned__ = {}

    id = db.Column(db.Integer, primary_key=True)
    tag_id = db.Column(db.String(50), db.ForeignKey("tags.tag"))
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"))

    tag = db.relationship("Tag", back_populates="events_with_tag")
    event = db.relationship("Event", back_populates="event_tags")
    creator_id = db.Column(UUID, db.ForeignKey("users.id"))
    creator = db.relationship("User", back_populates="created_event_tags")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @hybrid_property
    def count(self):
        return len(self.tag.events_with_tag)

    @count.expression
    def count(cls):
        return (
            select([func.count(EventTag.tag_id)])
            .where(EventTag.tag_id == cls.tag_id)
            .correlate(Tag)
            .label("count")
        )
