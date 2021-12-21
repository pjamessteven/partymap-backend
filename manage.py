"""
manage.py
- provides a command line utility for interacting with the
  application to perform interactive debugging and setup
"""

from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from flask.helpers import get_debug_flag

# from utils.populate_db import Populate
# from utils.clustering import ClusterEventLocations
from pmapi.application import create_app
from pmapi.extensions import db
from pmapi.config import ProdConfig, DevConfig

# export FLASK_DEBUG=1 for dev
CONFIG = DevConfig if get_debug_flag() else ProdConfig

app = create_app(CONFIG)

migrate = Migrate(app, db)
manager = Manager(app)

# provide a migration utility command
manager.add_command("db", MigrateCommand)
# manager.add_command("populate", Populate)
# manager.add_command("cluster", ClusterEventLocations)


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
