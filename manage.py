"""
manage.py
- provides a command line utility for interacting with the
  application to perform interactive debugging and setup
"""

# Monkey-patch flask._compat for Flask 2+ compatibility with flask-script
import sys
import flask
if not hasattr(flask, '_compat'):
    import types
    compat = types.ModuleType('flask._compat')
    compat.text_type = str
    compat.string_types = (str,)
    compat.integer_types = (int,)
    compat.iteritems = lambda d: d.items()
    compat.iterkeys = lambda d: d.keys()
    compat.itervalues = lambda d: d.values()
    flask._compat = compat
    sys.modules['flask._compat'] = compat

from flask_script import Manager, Command, Option
from flask_migrate import Migrate, MigrateCommand
from flask.helpers import get_debug_flag
from flask.cli import FlaskGroup
from sqlalchemy import exc
from pmapi.application import create_app
from pmapi.extensions import db
from pmapi.config import ProdConfig, DevConfig
from pmapi.utils import ROLES
from seed_db import SeedTestDb
from typemallow2 import generate_ts

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
        print("Creating users...")
        from pmapi.user.model import User
        try:
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
            print("Created users: ",  anon, system, admin)
        except exc.SQLAlchemyError:
            print("There was en error creating users, perhaps they already exist.")


# seed database with prod db snapshot (july 2022)
# so that we can have some real events, artists and tags 
# to test with 

class GenerateTypes(Command):
    def run(self):
        generate_ts('./autogen_types.ts')


class BackfillEventEmbeddings(Command):
    option_list = (
        Option("--batch-size", dest="batch_size", type=int, default=100),
        Option("--limit", dest="limit", type=int, default=None),
        Option("--force", action="store_true", dest="force", default=False),
    )

    def run(self, batch_size, limit, force):
        from scripts.backfill_event_embeddings import run_backfill

        run_backfill(
            batch_size=batch_size,
            limit=limit,
            force=force,
            logger=app.logger,
        )


manager.add_command("create_db", CreateDb)
manager.add_command("create_users", CreateUsers)
manager.add_command("seed_test_db", SeedTestDb)
manager.add_command("generate_types", GenerateTypes)
manager.add_command("backfill_event_embeddings", BackfillEventEmbeddings)

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
    # Patch for Python 3.12 compatibility with flask-script
    import argparse
    original_parse_known_args = argparse.ArgumentParser.parse_known_args
    
    def patched_parse_known_args(self, args=None, namespace=None):
        if namespace is None:
            namespace = argparse.Namespace()
        return original_parse_known_args(self, args, namespace)
    
    argparse.ArgumentParser.parse_known_args = patched_parse_known_args
    
    manager.run()
