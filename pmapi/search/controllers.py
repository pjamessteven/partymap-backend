from pmapi import exceptions as exc
from pmapi.extensions import db, activity_plugin
from datetime import datetime
from flask_login import current_user, login_user
from sqlalchemy_continuum import version_class, transaction_class
from sqlalchemy import cast, or_, and_, func, select, join
from sqlalchemy.orm import with_expression
from pmapi.event_date.model import EventDate
from pmapi.event.model import Event
from pmapi.event_tag.model import Tag
from pmapi.event_artist.model import Artist
from pmapi.event_location.model import Country, Region, Locality
import pmapi.user.controllers as users


Activity = activity_plugin.activity_cls


def search(query):
    """
    experiment with this later
    query_text = ""
    for word in query_string.split():
        # this is to formulate a query string like 'twisted:* frequncey:*'
        if word == query_string.split()[-1]:
            query_text = query_text + (str(word) + str(":*"))
        else:
            query_text = query_text + (str(word) + str(":* & "))
    """
    search = "%{}%".format(query)

    tags = db.session.query(Tag).filter(Tag.tag.ilike(search)).all()[:3]
    artists = db.session.query(Artist).filter(Artist.name.ilike(search)).all()[:3]
    events = db.session.query(Event).filter(Event.name.ilike(search)).filter(Event.hidden == False).all()[:3]
    countries = (
        db.session.query(Country).filter(Country.long_name.ilike(search)).all()[:1]
    )
    regions = db.session.query(Region).filter(Region.full_name.ilike(search)).all()[:3]
    localities = (
        db.session.query(Locality).filter(Locality.full_name.ilike(search)).all()
    )[:3]

    results = []

    for tag in tags:
        results.append({"type": "tag", "result": tag.tag})
    for artist in artists:
        results.append({"type": "artist", "result": artist.name, "id": artist.id})
    for event in events:
        results.append({"type": "event", "result": event.name, "id": event.id})
    """
    for country in countries:
        results.append(
            {
                "type": "country",
                "result": country.long_name,
            }
        )
    for region in regions:
        results.append({"type": "region", "result": region.full_name})
    for locality in localities:
        results.append({"type": "locality", "result": locality.full_name})
    """
    return {"results": results}
