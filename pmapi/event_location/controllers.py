import reverse_geocode
import pygeohash as pgh
from sqlalchemy import or_, and_

from pmapi.event_location.model import EventLocation, EventLocationType
from pmapi.extensions import db
from pmapi.event_date.model import EventDate
from pmapi.event_tag.model import EventTag
from pmapi.event.model import Event
from pmapi.common.controllers import paginated_results
from pmapi import exceptions as exc


def add_new_event_location(**location):

    geometry = location.get("geometry")
    name = location.get("name")
    description = location.get("description")
    place_id = location.get("place_id")
    types = location.get("types")

    lat = float(geometry["location"]["lat"])
    lng = float(geometry["location"]["lng"])

    geocode = reverse_geocode.search([(lat, lng)])[0]

    location_type_objects = []
    for t in types:
        type = None
        if (
            db.session.query(EventLocationType)
            .filter(EventLocationType.type == t)
            .count()
        ):
            type = (
                db.session.query(EventLocationType)
                .filter(EventLocationType.type == t)
                .one()
            )
        else:
            type = EventLocationType(type=t)
            db.session.add(type)

        location_type_objects.append(type)

    location = EventLocation(
        geohash=pgh.encode(lat, lng),
        # For geodetic coordinates,
        # X is longitude and Y is latitude
        geo="SRID=4326;POINT ({0} {1})".format(lng, lat),
        name=name,
        description=description,
        types=location_type_objects,
        lat=lat,
        lng=lng,
        country_code=geocode["country_code"],
        city=geocode["city"],
        place_id=place_id,
    )

    # merging - is this ok?
    return db.session.add(location)
    db.session.commit()


def get_location_or_404(place_id):
    location = get_location(place_id)
    if not location:
        msg = "No such location with place_id {}".format(place_id)
        raise exc.RecordNotFound(msg)
    return location


def get_location(place_id):
    return EventLocation.query.get(place_id)


def get_all_locations(**kwargs):

    query = db.session.query(
        EventLocation
    ).distinct()  # fixes issues related to pagination

    if "date_min" in kwargs or "date_max" in kwargs:
        query = query.join(EventDate)
    if "date_min" in kwargs:
        query = query.filter(EventDate.event_start_naive >= kwargs.pop("date_min"))
    if "date_max" in kwargs:
        date_max = kwargs.pop("date_max")
        query = query.filter(
            and_(
                or_(
                    EventDate.event_end_naive <= date_max,
                    EventDate.event_end_naive.is_(None),
                ),
                EventDate.event_start_naive <= date_max,
            )
        )

    if "tags" in kwargs:
        tags = kwargs.pop("tags")
        query = query.join(Event)
        for tag in tags:
            query = query.filter(Event.event_tags.any(EventTag.tag_id == tag))
    return query


def get_all_locations_paginated(**kwargs):
    query = get_all_locations(**kwargs)
    return paginated_results(EventLocation, query=query, **kwargs)
