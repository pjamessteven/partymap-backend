from pmapi.extensions import db

favorites_association_table = db.Table('favorites_association',
                                       db.Column('user', db.Integer,
                                                 db.ForeignKey('users.id')),
                                       db.Column('event', db.Integer,
                                                 db.ForeignKey('events.id'))
                                       )
