from pmapi.extensions import db
from sqlalchemy.dialects.postgresql import UUID

favorites_association_table = db.Table('favorites_association',
                                       db.Column('user', UUID,
                                                 db.ForeignKey('users.id')),
                                       db.Column('event', UUID,
                                                 db.ForeignKey('events.id'))
                                       )
