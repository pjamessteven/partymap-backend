from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_, and_
from flask_script import Command
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.query import Query
from flask import (
    Blueprint,
    jsonify,
    request,
    Flask,
    redirect,
    flash,
    url_for,
    current_app,
    send_from_directory,
)
from pmapi.user.model import User
from pmapi.event_tag.model import EventTag, Tag
from pmapi.event_image.model import EventImage
from pmapi.event.model import Event, Rrule
from pmapi.event_date.model import EventDate
from pmapi.event_location.model import EventLocation
from pmapi.extensions import db, lm
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    current_user,
    login_required,
)

import random
import string
from timezonefinder import TimezoneFinder
import pygeohash as pgh
from geoalchemy2 import Geometry
from datetime import datetime, timedelta


class Populate(Command):
    def run(self):
        user = db.session.query(User).first()
        login_user(user, remember=True)
        print(current_user)

        # generate a bunch of random tags
        tags = []
        for x in range(2000):
            tag = self.randomString()
            tags.append(tag)

        for x in range(10000):
            lat = random.randint(21, 45)
            lng = random.randint(80, 107)
            tf = TimezoneFinder()
            event_start_timestamp = random.randint(1575817003, 1670511403)
            event_start = datetime.fromtimestamp(event_start_timestamp)
            event_end = datetime.fromtimestamp(
                event_start_timestamp + 1000000
            )  # add about 12 days

            location = EventLocation(
                geohash=pgh.encode(lat, lng),
                # For geodetic coordinates, X is longitude and Y is latitude
                geo="SRID=4326;POINT ({0} {1})".format(lng, lat),
                name="test location",
                lat=lat,
                lng=lng,
                country_code="NZ",
                city="Timaru",
            )

            event = Event(
                name=random.choice(tags),
                creator_id=1,
                default_url=random.choice(tags),
                default_description=random.choice(tags),
                locations=[location],
            )

            # merging - is this ok?
            event = db.session.merge(event)
            location = db.session.merge(location)
            db.session.flush()

            # add a random amount of random tags

            for x in range(0, random.randint(0, 10)):
                t = random.choice(tags)
                tag = Tag(tag=t)
                # check if tag is already in db
                if db.session.query(Tag).filter(Tag.tag == t).count():
                    tag = db.session.query(Tag).filter(Tag.tag == t).one()

                if (
                    db.session.query(EventTag)
                    .filter(EventTag.tag == tag, EventTag.event == event)
                    .count()
                ):
                    # event already has tag
                    pass
                else:
                    et = EventTag(tag=tag, event=event)
                    db.session.add(et)

            event.recurring = False
            tz = tf.timezone_at(lng=lng, lat=lat)
            if tz is None:
                tz = "not found"
                print("tz not found")

            ed = EventDate(
                event_id=event.id,
                event=event,
                event_end=event_end,
                event_start=event_start,
                tz=tz,
                location=location,
            )
            db.session.add(ed)
            db.session.commit()

    def randomString(self, stringLength=2):
        """Generate a random string of fixed length """
        letters = string.ascii_lowercase
        return "".join(random.choice(letters) for i in range(stringLength))
