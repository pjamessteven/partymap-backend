import reverse_geocode
import pygeohash as pgh
from sqlalchemy.orm import with_expression
from sqlalchemy.orm import subqueryload, selectinload, joinedload, Bundle
from sqlalchemy import select, func, distinct, String, Text, join
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import or_, and_

from pmapi.event_location.model import EventLocation, EventLocationType
from pmapi.extensions import db
from pmapi.event_date.model import EventDate
from pmapi.event_tag.model import EventTag
from pmapi.event.model import Event
from pmapi.common.controllers import paginated_results
from pmapi import exceptions as exc


def add_new_event_location(creator=None, **kwargs):

    geometry = kwargs.get("geometry")
    name = kwargs.get("name")
    description = kwargs.get("description")
    place_id = kwargs.get("place_id")
    types = kwargs.get("types")
    address_components = kwargs.get("address_components")

    lat = float(geometry["location"]["lat"])
    lng = float(geometry["location"]["lng"])

    # return location if it already exists
    if (get_location(place_id)) is not None:
        return get_location(place_id)

    geocode = reverse_geocode.search([(lat, lng)])[0]

    location_type_objects = []
    db.session.flush()
    for t in types:
        print(t)
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
    print(location_type_objects)
    db.session.flush()
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
        creator=creator,
        address_components=address_components,
    )
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
    print()
    result = EventLocation.query.filter(EventLocation.place_id == place_id).first()
    print(result)
    return result


def get_all_locations(**kwargs):

    query = db.session.query(EventLocation)

    if "date_min" in kwargs or "date_max" in kwargs or "tags" in kwargs:
        # this expression allows us to show the events for a given
        # event_location in the query
        expression = select(
            [
                func.array_agg(
                    distinct(  # remove duplicate eventdates at same location
                        func.jsonb_build_object("name", Event.name, "id", Event.id)
                    )
                )
            ]
        ).select_from(join(Event, EventDate))

        query = (
            db.session.query(EventLocation)
            .join(EventLocation.event_dates)
            .join(EventDate.event)
            .populate_existing()
            .distinct()
        )  # fixes issues related to pagination
        if "date_min" in kwargs:
            datemin = kwargs.pop("date_min")
            query = query.filter(EventDate.start_naive >= datemin)
            expression = expression.where(EventDate.start_naive >= datemin)
        if "date_max" in kwargs:
            date_max = kwargs.pop("date_max")
            query = query.filter(
                EventDate.start_naive <= date_max,
            )
            expression = expression.where(EventDate.start_naive <= date_max)

        if "duration_options" in kwargs:
            duration_options = kwargs.pop("duration_options")
            search_args = [EventDate.duration == option for option in duration_options]
            query = query.filter(or_(*search_args))

        if "size_options" in kwargs:
            size_options = kwargs.pop("size_options")
            size_options_parsed = []
            for size in size_options:
                chunks = size.split(",")
                size_options_parsed.append([chunks[0], chunks[1]])
            search_args = [
                and_(EventDate.size >= range[0], EventDate.size <= range[1])
                for range in size_options_parsed
            ]
            query = query.filter(or_(*search_args))

        if "tags" in kwargs:
            tags = kwargs.pop("tags")
            for tag in tags:
                query = query.filter(Event.event_tags.any(EventTag.tag_id == tag))
                expression = expression.where(
                    Event.event_tags.any(EventTag.tag_id == tag)
                )

        # filter cancelled events out
        query = query.filter(EventDate.cancelled != True)

        # filter hidden events out
        query = query.filter(Event.hidden == False)  # ignore linter warning here

        return query.options(
            with_expression(
                EventLocation.events,
                expression.where(EventDate.location_id == EventLocation.id),
            )
        )


def get_all_locations_paginated(**kwargs):
    query = get_all_locations(**kwargs)
    return paginated_results(EventLocation, query=query, **kwargs)
