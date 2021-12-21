from .application import create_app
from .extensions import db
from .config import DevConfig
from .config import ProdConfig
from flask.helpers import get_debug_flag
import click
from flask.cli import with_appcontext

DEV_ENVIRON = get_debug_flag()

CONFIG = DevConfig if DEV_ENVIRON else ProdConfig

app = create_app(CONFIG)


# to run: flask seed_db
@app.cli.command()
def seed_db():
    _seed_db()


app.cli.add_command(seed_db)


def _seed_db():
    """Seed the db with admin account and anon account"""
    from pmapi.user.models import User

    admin_id = "75167075-4371-4fc6-9b59-5c67d183abda"
    anon_id = "ac858dc2-2018-4de2-9975-3d716030eb72"

    admin = User(
        id=admin_id,
        username="admin",
        email="admin@partymap.com",
        password="A110BCC274257310AAA20961952EE6F8A9ED8E2D8917F790D76CCCE2970D8066",
        role=30,
        status="active",
    )

    anon = User(
        id=anon_id,
        username="anonymous",
        email="anon@partymap.com",
        role=0,
        status="active",
    )

    with app.app_context():
        db.session.add(admin)
        db.session.add(anon)
        if DEV_ENVIRON:
            admin.set_password("admin")

        db.session.flush()
        db.session.commit()
