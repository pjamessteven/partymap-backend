import reverse_geocode
import pygeohash as pgh
from flask_login import current_user
from pmapi.event_location.model import EventLocation, EventLocationType
from pmapi.extensions import db
from pmapi.event_date.model import EventDate
from pmapi.event_tag.model import EventTag
from pmapi.event.model import Event
from pmapi.common.controllers import paginated_results
from pmapi import exceptions as exc


def add_new_event_location(user=current_user, **kwargs):

    geometry = kwargs.get("geometry")
    name = kwargs.get("name")
    description = kwargs.get("description")
    place_id = kwargs.get("place_id")
    types = kwargs.get("types")

    lat = float(geometry["location"]["lat"])
    lng = float(geometry["location"]["lng"])

    if get_location(place_id) is not None:
        raise exc.RecordAlreadyExists()

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

    db.session.commit()
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
        country=geocode["country"],
        country_code=geocode["country_code"],
        city=geocode["city"],
        place_id=place_id,
        creator_id=user.id,
    )
    # merging - is this ok?
    db.session.add(location)
    db.session.commit()
    return location


def get_location_or_404(place_id):
    location = get_location(place_id)
    if not location:
        msg = "No such location with place_id {}".format(place_id)
        raise exc.RecordNotFound(msg)
    return location


def get_location(place_id):
    return EventLocation.query.get(place_id)


def get_all_locations(**kwargs):

    query = (
        db.session.query(EventLocation).join(EventDate).distinct()
    )  # fixes issues related to pagination

    if "date_min" in kwargs:
        query = query.filter(EventDate.event_start_naive >= kwargs.pop("date_min"))
    if "date_max" in kwargs:
        date_max = kwargs.pop("date_max")
        query = query.filter(
            EventDate.event_start_naive <= date_max,
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
