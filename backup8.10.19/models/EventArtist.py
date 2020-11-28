from pmapi.application import db
import calendar
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user

event_artist_upvotes = db.Table('event_artist_upvotes',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('event_artist_name', db.String, db.ForeignKey('event_artists.artist_name')),
    db.Column('event_artist_event_id', db.Integer, db.ForeignKey('event_artists.event_date_id'))
)

event_artist_downvotes = db.Table('event_artist_downvotes',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
    db.Column('event_artist_name', db.String, db.ForeignKey('event_artists.artist_name')),
    db.Column('event_artist_event_id', db.Integer, db.ForeignKey('event_artists.event_date_id'))
)

# tag is the parent of event
class Artist(db.Model):
    __tablename__ = 'artists'
    #this is fine, two artists can share the same page. best solution.
    name = db.Column(db.String(50), primary_key=True, nullable=False)
    events_with_artist = db.relationship('EventArtist', back_populates="artist")
    created_at = db.Column(db.DateTime, default=datetime.utcnow())

    #artist specific stuff

    description = db.Column(db.Text)
    urls = db.Column(db.Text) #no json type :(

    #relationship with eventimage?

    def to_dict(self):
        count = 0
        for event in self.events_with_artist:
            count+=1
        return dict(text=self.name,
                    created_at=self.created_at,
                    description=self.description,
                    urls=self.urls
        )



#when adding an event tag, only need to specify votes, tag and event. PKs are automatic. Somehow..
class EventArtist(db.Model):
    __tablename__ = 'event_artists'

    artist_name = db.Column(db.String(50), db.ForeignKey('artists.name'), primary_key=True)
    event_date_id = db.Column(db.Integer, db.ForeignKey('event_dates.id'), primary_key=True)

    artist = db.relationship('Artist', back_populates="events_with_artist")
    event_date = db.relationship('EventDate', back_populates="event_artists")
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow())

    status = db.Column(db.SmallInteger, default=1)
    votes = db.Column(db.Integer, default=0)
    hotness = db.Column(db.Float(15,6), default=0.00)

    def to_dict(self):
        artist = self.artist.to_dict()
        if current_user.is_authenticated:
            return dict(artist = artist,
                    #for easier tag sorting
                    text = artist['text'],
                    event = self.event.id,
                    votes = self.votes,
                    has_voted = self.has_voted(current_user.id)
                    )
        else:
            return dict(artist = artist,
                    #for easier tag sorting
                    text = artist['text'],
                    event = self.event.id,
                    votes = self.votes,
                    )


    def get_status(self):
        """
        returns string form of status, 0 = 'dead', 1 = 'alive'
        """
        return self.status

    def get_hotness(self):
        """
        returns the reddit hotness algorithm (votes/(age^1.5))
        """
        order = log(max(abs(self.votes), 1), 10) # Max/abs are not needed in our case
        seconds = self.get_age() - 1134028003
        return round(order + seconds / 45000, 6)

    def set_hotness(self):
        """
        returns the reddit hotness algorithm (votes/(age^1.5))
        """
        self.hotness = self.get_hotness()
        db.session.commit()

    def pretty_date(self):
        """
        returns a humanized version of the raw age of this item,
        eg: 34 minutes ago versus 2040 seconds ago.
        """
        return utils.pretty_date(self.created_at)

    def get_upvoter_ids(self):
        """
        return ids of users who voted this item up
        """
        # select = event_artist_upvotes.select(event_artist_upvotes.c.thread_id==self.id)
        select = event_artist_upvotes.select(
            db.and_(
                event_artist_upvotes.c.event_artist_name == self.artist_name,
                event_artist_upvotes.c.event_artist_event_id == self.event_id
            ))
        rs = db.engine.execute(select)
        ids = rs.fetchall() # list of tuples
        return ids

    def get_downvoter_ids(self):
        """
        return ids of users who voted this item down
        """
        # select = event_artist_upvotes.select(event_artist_upvotes.c.thread_id==self.id)
        select = event_artist_downvotes.select(
            db.and_(
                event_artist_downvotes.c.event_artist_name == self.artist_name,
                event_artist_downvotes.c.event_artist_event_id == self.event_id
            ))
        rs = db.engine.execute(select)
        ids = rs.fetchall() # list of tuples
        return ids

    def has_voted(self, user_id):
        """
        did the user vote already? will return 1 if upvoted, -1 if downvoted and 0 if not voted.
        """
        print('TAGVOTEDFUNC')
        select_upvotes = event_artist_upvotes.select(
                db.and_(
                    event_artist_upvotes.c.user_id == user_id,
                    event_artist_upvotes.c.event_artist_name == self.artist_name,
                    event_artist_upvotes.c.event_artist_event_id == self.event_id
                )
        )
        select_downvotes = event_artist_downvotes.select(
                db.and_(
                    event_artist_downvotes.c.user_id == user_id,
                    event_artist_downvotes.c.event_artist_name == self.artist_name,
                    event_artist_downvotes.c.event_artist_event_id == self.event_id
                )
        )
        rs = db.engine.execute(select_upvotes).fetchall()
        rs1 = db.engine.execute(select_downvotes).fetchall()

        print(len(rs))
        if len(rs) > 0:
            print("has upvoted")
            return 1
        elif len(rs1) > 0:
            print("has downvoted")
            return -1
        else:
            print("has not voted")
            return 0

    def vote(self, user_id, vote):
        """
        allow a user to vote on an item. if we have voted already
        (and they are clicking again), this means that they are trying
        to unvote the item, return status of the vote for that user
        """
        already_voted = self.has_voted(user_id)
        vote_status = None
        #if user hasn't already voted
        if already_voted==0:
            if vote == 1:
                # vote up the item
                db.engine.execute(
                    event_artist_upvotes.insert(),
                    user_id   = user_id,
                    event_artist_name = self.artist_name,
                    event_artist_event_id = self.event_id
                    )
                self.votes = self.votes + 1
                vote_status = 1
            elif vote == -1:
                #downvote the item
                db.engine.execute(
                    event_artist_downvotes.insert(),
                    user_id   = user_id,
                    event_artist_name = self.artist_name,
                    event_artist_event_id = self.event_id
                    )
                self.votes = self.votes - 1
                vote_status = -1
            else:
                return None
        #if they have already upvoted
        elif already_voted==1:
            #and they have selected upvote again
            if vote==1:
                # unvote the item
                db.engine.execute(
                    event_artist_upvotes.delete(
                        db.and_(
                            event_artist_upvotes.c.user_id == user_id,
                            event_artist_upvotes.c.event_artist_name == self.artist_name,
                            event_artist_upvotes.c.event_artist_event_id == self.event_id
                        )
                    )
                )
                self.votes = self.votes - 1
                vote_status = -1
            #and they now select downvote instead
            elif vote==-1:
                # unvote the item
                db.engine.execute(
                    event_artist_upvotes.delete(
                        db.and_(
                            event_artist_upvotes.c.user_id == user_id,
                            event_artist_upvotes.c.event_artist_name == self.artist_name,
                            event_artist_upvotes.c.event_artist_event_id == self.event_id
                        )
                    )
                )
                self.votes = self.votes - 1
                #and now add a downvote
                db.engine.execute(
                    event_artist_downvotes.insert(),
                    user_id   = user_id,
                    event_artist_name = self.artist_name,
                    event_artist_event_id = self.event_id
                )
                self.votes = self.votes - 1
                vote_status = -2
            else:
                return None
        #if they have already downvoted
        elif already_voted==-1:
            #and they select downvote again
            if vote==-1:
                # undownvote the item
                db.engine.execute(
                    event_artist_downvotes.delete(
                        db.and_(
                            event_artist_downvotes.c.user_id == user_id,
                            event_artist_downvotes.c.event_artist_name == self.artist_name,
                            event_artist_downvotes.c.event_artist_event_id == self.event_id
                        )
                    )
                )
                self.votes = self.votes + 1
                vote_status = 1
            elif vote==1:
                #undownvote the item
                db.engine.execute(
                    event_artist_downvotes.delete(
                        db.and_(
                            event_artist_downvotes.c.user_id == user_id,
                            event_artist_downvotes.c.event_artist_name == self.artist_name,
                            event_artist_downvotes.c.event_artist_event_id == self.event_id
                        )
                    )
                )
                self.votes = self.votes + 1
                #then add an upvote
                db.engine.execute(
                    event_artist_upvotes.insert(),
                    user_id   = user_id,
                    event_artist_name = self.artist_name,
                    event_artist_event_id = self.event_id
                )
                self.votes = self.votes + 1
                vote_status = +2
            else:
                return None
        db.session.commit() # for the vote count
        return vote_status
