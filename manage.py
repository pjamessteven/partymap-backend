"""
manage.py
- provides a command line utility for interacting with the
  application to perform interactive debugging and setup
"""

from flask_script import Manager, Command
from flask_migrate import Migrate, MigrateCommand
from flask.helpers import get_debug_flag
from flask.cli import FlaskGroup
# from utils.populate_db import Populate
# from utils.clustering import ClusterEventLocations
from pmapi.application import create_app
from pmapi.extensions import db
from pmapi.config import ProdConfig, DevConfig
from pmapi.utils import ROLES
from seed_db import SeedTestDb
# export FLASK_DEBUG=1 for dev
CONFIG = DevConfig if get_debug_flag() else ProdConfig

app = create_app(CONFIG)
cli = FlaskGroup(app)
migrate = Migrate(app, db)
manager = Manager(app)

# provide a migration utility command
manager.add_command("db", MigrateCommand)

# manager.add_command("populate", Populate)
# manager.add_command("cluster", ClusterEventLocations)
class CreateDb(Command):
    def run(self):
        db.create_all()
        db.session.commit()

class CreateUsers(Command):
    def run(self):
        from pmapi.user.model import User
        anon = User(
            username="anon",
            email="anon@partymap.com",
            status="active",
            id=CONFIG.ANON_USER_ID,
        )
        system = User(
            username="partymap-bot",
            email="info@partymap.com",
            status="active",
            id=CONFIG.SYSTEM_USER_ID,
        )
        admin = User(
            username="admin",
            email="admin@partymap.com",
            status="active",
            role=ROLES["ADMIN"]
        )
        admin.set_password('password')
        db.session.add(anon)
        db.session.add(system)
        db.session.add(admin)
        db.session.commit()

# seed database with prod db snapshot (july 2022)
# so that we can have some real events, artists and tags 
# to test with 

   


manager.add_command("create_db", CreateDb)
manager.add_command("create_users", CreateUsers)
manager.add_command("seed_test_db", SeedTestDb)

# enable python shell with application context
@manager.shell
def shell_ctx():
    from pmapi.event_tag.model import Tag, EventTag
    from pmapi.event.model import Event, Rrule
    from pmapi.user.model import User
    from pmapi.media.model import MediaItem
    from pmapi.event_artist.model import EventDateArtist, Artist, ArtistUrl
    from pmapi.report.model import Report
    from pmapi.event_location.model import EventLocation
    from pmapi.event_date.model import EventDate
    from pmapi.suggestions.model import SuggestedEdit
    from pmapi.notification.model import Notification, UserNotification, EmailAction
    from pmapi.extensions import db, activity_plugin

    Activity = activity_plugin.activity_cls

    return dict(
        app=app,
        db=db,
        Tag=Tag,
        Activity=Activity,
        Event=Event,
        User=User,
        MediaItem=MediaItem,
        EventTag=EventTag,
        EventDate=EventDate,
        EventLocation=EventLocation,
        Rrule=Rrule,
        Report=Report,
        Notification=Notification,
        UserNotification=UserNotification,
        EmailAction=EmailAction,
        SuggestedEdit=SuggestedEdit,
        EventDateArtist=EventDateArtist,
        Artist=Artist,
        ArtistUrl=ArtistUrl,
    )


if __name__ == "__main__":
    manager.run()
