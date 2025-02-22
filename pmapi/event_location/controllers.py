import reverse_geocode
import pygeohash as pgh
from flask_login import current_user
from sqlalchemy.sql import union_all
from sqlalchemy.orm import with_expression
from sqlalchemy.orm import subqueryload, selectinload, joinedload, Bundle
from sqlalchemy import select, func, distinct, asc, String, Text, join
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import or_, and_
from sqlalchemy.sql.expression import literal
from pmapi.event_location.model import (
    EventLocation,
    EventLocationType,
    Country,
    Region,
    Locality,
)
from pmapi.extensions import db
from pmapi.event_date.model import EventDate
from pmapi.event_tag.model import EventTag
from pmapi.event_artist.model import EventDateArtist
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

    # return location if it already exists
    if (get_location(place_id)) is not None:
        return get_location(place_id)

    country = None
    region = None
    locality = None

    # get country
    for component in address_components:
        if "country" in component["types"]:
            short_name = component["short_name"]
            existing_country = get_country(short_name)
            if existing_country is not None:
                country = existing_country
            else:
                country = Country(
                    short_name=component["short_name"], long_name=component["long_name"]
                )
                db.session.add(country)
                db.session.flush()

    # get region
    for component in address_components:
        if "administrative_area_level_1" in component["types"]:
            short_name = component["short_name"]
            existing_region_of_country = get_region_of_country(
                short_name, country)
            if existing_region_of_country is not None:
                region = existing_region_of_country
            else:
                region = Region(
                    short_name=component["short_name"],
                    long_name=component["long_name"],
                    country=country,
                )
                db.session.add(region)
                db.session.flush()

    # get locality
    for component in address_components:
        if "locality" in component["types"]:
            short_name = component["short_name"]
            existing_locality_of_region_of_country = get_locality_of_region_of_country(
                short_name, region, country
            )
            if existing_locality_of_region_of_country is not None:
                locality = existing_locality_of_region_of_country
            else:
                locality = Locality(
                    short_name=component["short_name"],
                    long_name=component["long_name"],
                    region=region,
                    country=country,
                )
                db.session.add(locality)
                db.session.flush()

    if (region is None and locality is None) or country is None:
        raise exc.InvalidAPIRequest(
            "A more specific location is required. Please try again."
        )

    lat = float(geometry["location"]["lat"])
    lng = float(geometry["location"]["lng"])

    # geocode = reverse_geocode.search([(lat, lng)])[0]

    location_type_objects = []
    db.session.flush()

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

    db.session.flush()
    creator_id = None
    if creator:
        creator_id = creator.id
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
        country=country,
        region=region,
        locality=locality,
        # country=geocode["country"],
        # country_code=geocode["country_code"],
        # city=geocode["city"],
        place_id=place_id,
        creator_id=creator_id,
        address_components=address_components,
    )
    db.session.add(location)
    db.session.flush()
    return location


def get_location_or_404(place_id):
    location = get_location(place_id)
    if not location:
        msg = "No such location with place_id {}".format(place_id)
        raise exc.RecordNotFound(msg)
    return location


def get_all_countries():
    return db.session.query(Country).order_by(Country.short_name.asc()).all()

def get_all_countries_with_future_event_count():

    # Query for individual countries
    country_query = (
        db.session.query(
            Country.short_name.label("short_name"),  # Ensure this matches "name" label in `all_countries_query`
            func.count(func.distinct(EventDate.event_id)).label("event_count")  # Correct distinct counting
        )
        .join(EventLocation, EventDate.location_id == EventLocation.id)  # Adjust FK column names
        .join(Country, EventLocation.country_id == Country.short_name)  # Ensure proper FK relationship
        .join(Event, Event.id == EventDate.event_id)  # Join Event with EventDate
        .filter(
            or_(
                and_(
                    EventDate.end.is_(None),  # Event.end is NULL
                    EventDate.start > func.now()  # Event.start > NOW()
                ),
                EventDate.end > func.now()  # Event.end is in the future
            )
        )
        .group_by(Country.short_name)
        .order_by(func.count(func.distinct(EventDate.event_id)).desc())  # Sort by event count in descending order
    )

    # Query for all countries combined
    all_countries_query = (
        db.session.query(
            literal("ALL_COUNTRIES").label("short_name"),  # Label for 'all countries'
            func.count(func.distinct(EventDate.event_id)).label("event_count")  # Correct distinct counting
        )
        .join(EventLocation, EventDate.location_id == EventLocation.id)  # Adjust FK column names
        .join(Event, Event.id == EventDate.event_id)  # Join Event with EventDate
        .filter(
            or_(
                and_(
                    EventDate.end.is_(None),  # Event.end is NULL
                    EventDate.start > func.now()  # Event.start > NOW()
                ),
                EventDate.end > func.now()  # Event.end is in the future
            )
        )
    )

    # Combine the two queries using UNION ALL
    combined_query = union_all(all_countries_query, country_query)

    # Execute the combined query
    result = db.session.execute(combined_query).all()

    return result

def get_all_country_regions_with_future_event_count(country_id):

    region_query = (
        db.session.query(
            Region.short_name.label("short_name"),  # Replace with the actual column for region name
            Region.long_name.label("long_name"),  # Replace with the actual column for region name
            Country.short_name.label("country"),  # Include country for context
            func.count(func.distinct(EventDate.event_id)).label("event_count")  # Count distinct events
        )
        .join(EventLocation, EventDate.location_id == EventLocation.id)  # Adjust FK column names
        .join(Region, EventLocation.region_id == Region.id)  # Join EventLocation with Region
        .join(Country, Region.country_id == Country.short_name)  # Ensure Region is associated with Country
        .join(Event, Event.id == EventDate.event_id)  # Join Event with EventDate
        .filter(Country.short_name == country_id)
        .filter(
            or_(
                and_(
                    EventDate.end.is_(None),  # Event.end is NULL
                    EventDate.start > func.now()  # Event.start > NOW()
                ),
                EventDate.end > func.now()  # Event.end is in the future
            )
        )
        .group_by(Region.short_name, Region.long_name, Country.short_name)  # Group by region and country
        .order_by(func.count(func.distinct(EventDate.event_id)).desc())  # Sort by event count in descending order
    )

    # Query for all countries combined
    all_regions_query = (
        db.session.query(
            literal("ALL_REGIONS").label("short_name"),  # Label for 'all countries'
            literal("ALL_REGIONS").label("long_name"),  # Label for 'all countries'
            Country.short_name.label("country"),  # Include country for context
            func.count(func.distinct(EventDate.event_id)).label("event_count")  # Correct distinct counting
        )
        .join(EventLocation, EventDate.location_id == EventLocation.id)  # Adjust FK column names
        .join(Region, EventLocation.region_id == Region.id)  # Join EventLocation with Region
        .join(Country, Region.country_id == Country.short_name)  # Ensure Region is associated with Country
        .join(Event, Event.id == EventDate.event_id)  # Join Event with EventDate
        .filter(Country.short_name == country_id)
        .filter(
            or_(
                and_(
                    EventDate.end.is_(None),  # Event.end is NULL
                    EventDate.start > func.now()  # Event.start > NOW()
                ),
                EventDate.end > func.now()  # Event.end is in the future
            )
        )
        .group_by(Country.short_name)
    )

    # Combine the two queries using UNION ALL
    combined_query = union_all(all_regions_query, region_query)

    # Execute the combined query
    result = db.session.execute(combined_query).all()

    return result


def get_country(short_name):
    result = Country.query.filter(Country.short_name == short_name).first()
    return result


def get_region_of_country(short_name, country):
    for region in country.regions:
        if region.short_name == short_name:
            return region
    return None


def get_all_regions_of_country(country_short_name, **kwargs):
    country = get_country(country_short_name)
    return paginated_results(Region, query=country.regions, **kwargs)


def get_all_localities_of_region_of_country(country_short_name, region_short_name, **kwargs):
    country = get_country(country_short_name)
    for reg in country.regions:
        if region_short_name == region.short_name:
            return paginatied_results(Locality, query=query, **kwargs)


def get_locality_of_region_of_country(short_name, region, country):
    for reg in country.regions:
        if reg:
            if (reg.short_name == region.short_name) or (reg.long_name == region.long_name):
                for loc in reg.localities:
                    if loc.short_name == short_name:
                        return loc
    return None


def get_location(place_id):
    result = EventLocation.query.filter(
        EventLocation.place_id == place_id).first()
    return result


def get_all_locations(**kwargs):

    query = db.session.query(EventLocation)

    if "date_min" in kwargs or "date_max" in kwargs or "tags" in kwargs:
        # this expression allows us to show the events for a given
        # event_location in the query

        """
        j = join(Event, EventDate)
        j = join(j, EventLocation)
        expression = (
            select(
                [
                    EventLocation.id,
                    func.array_agg(
                        distinct(  # remove duplicate eventdates at same location
                            func.jsonb_build_object(
                                "name",
                                Event.name,
                                "event_id",
                                Event.id,
                                "event_date_id",
                                EventDate.id,
                            )
                        )
                    ),
                ]
            )
            .group_by(EventLocation.id)
            .select_from(j)
        )

        """

        j = join(Event, EventDate)
        # j = join(j, user_event_favorites_table)


        # an event having multiple locations is an edge case, find a better way to deal with this later
        expression = select(
            [
                func.array_agg(
                    distinct(  # remove duplicate eventdates at same location
                        func.jsonb_build_object(
                            "name",
                            Event.name,
                            "event_id",
                            Event.id,
                            # "event_date_id",
                            # EventDate.id,
                        )
                    )
                )
            ]
        ).select_from(j)

        query = (
            db.session.query(EventLocation)
            .join(EventLocation.event_dates)
            .join(EventDate.event)
            .populate_existing()
            .distinct()
        )  # fixes issues related to pagination

        if "date_min" in kwargs:
            datemin = kwargs.pop("date_min")
            query = query.filter(EventDate.start >= datemin)
            expression = expression.where(EventDate.start >= datemin)
        if "date_max" in kwargs:
            date_max = kwargs.pop("date_max")
            query = query.filter(
                EventDate.start <= date_max,
            )
            expression = expression.where(EventDate.start <= date_max)

        if "duration_options" in kwargs:
            duration_options = kwargs.pop("duration_options")
            search_args = [EventDate.duration ==
                           option for option in duration_options]
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
                query = query.filter(
                    Event.event_tags.any(EventTag.tag_id == tag))
                expression = expression.where(
                    Event.event_tags.any(EventTag.tag_id == tag)
                )

        if "artists" in kwargs:
            artists = kwargs.pop("artists")
            for artist_id in artists:
                query = query.filter(
                    EventDate.artists.any(
                        EventDateArtist.artist_id == artist_id)
                )
                expression = expression.where(
                    EventDate.artists.any(
                        EventDateArtist.artist_id == artist_id)
                )

        """ 
        # TODO 
        if kwargs.get("distinct", None) is True:
            print('distinct')
            # add row number column so we can filter
            # for the next occurance of an event date below
            row_number_column = (
                func.row_number()
                .over(partition_by=EventDate.event_id, order_by=asc(EventDate.start))
                .label("row_number")
            )
            subquery = query.add_column(
                row_number_column
            ).subquery()

            query = (
                db.session.query(subquery.c.EventLocation)
                .filter(subquery.c.row_number == 1)
                .distinct()
            )
        """
        if kwargs.get("empty_lineup", None) is True:
            query = query.filter(
                    ~EventDate.artists.any()
                )
            
        if kwargs.get("date_unconfirmed", None) is True:
            query = query.filter(
                    EventDate.date_confirmed == False
                )
            


        if kwargs.get("query", None) is not None:
            query_string = kwargs.pop("query")
            query_text = ""
            for word in query_string.split():
                # this is to formulate a query string like 'twisted:* frequncey:*'
                if word == query_string.split()[-1]:
                    query_text = query_text + (str(word) + str(":*"))
                else:
                    query_text = query_text + (str(word) + str(":* & "))
            query = query.filter(
                Event.__ts_vector__.match(
                    query_text, postgresql_regconfig="english")
            )
            expression = expression.where(
                Event.__ts_vector__.match(
                    query_text, postgresql_regconfig="english")
            )

        
    # filter cancelled events out
    # query = query.filter(EventDate.cancelled != True)

    # filter hidden events out
    query = query.filter(
        or_(
                    Event.hidden == False,
                    and_(
                        Event.hidden == True,
                        Event.creator_id is not None, 
                        Event.creator_id == current_user.id
                    )
                ))
    
    return query.options(
        with_expression(
            EventLocation.events,
            expression.where(EventDate.location_id == EventLocation.id),
        )
    )


"""
        if kwargs.get("favorites", None) is not None:
            if kwargs.get("favorites") is True:
                if not current_user.is_authenticated:
                    raise exc.InvalidAPIRequest("Login required for favorites")
                query = query.join(user_event_favorites_table).filter(
                    user_event_favorites_table.c.user_id == current_user.id
                )
                expression = expression.select_from(
                    join(expression.froms[0], user_event_favorites_table)
                )

                expression = expression.where(
                    user_event_favorites_table.c.user_id == current_user.id
                )
"""


def get_all_locations_paginated(**kwargs):
    query = get_all_locations(**kwargs)
    return paginated_results(EventLocation, query=query, **kwargs)
