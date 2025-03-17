import pytz
from pytz.exceptions import UnknownTimeZoneError
from pmapi.event_artist.controllers import add_artists_to_date, remove_artists_from_date, update_artists_of_date
from pmapi.event_location.schemas import ExtendedRegionSchema
from pmapi.event_review.model import EventReview
from timezonefinder import TimezoneFinder
from datetime import datetime
from flask_login import current_user
from flask import Response
from calendar import isleap
from icalendar import Calendar as icalendarCalendar, Event as icalendarEvent, vCalAddress, vText

from geoalchemy2 import func, Geography
from sqlalchemy import cast, or_, and_, asc, distinct
from sqlalchemy.orm import with_expression, aliased

from collections import Counter
from pmapi.common.controllers import paginated_results
import pmapi.event_location.controllers as event_locations
import pmapi.user.controllers as users
from pmapi.extensions import db, activity_plugin
from pmapi.event_location.model import EventLocation, Region
from pmapi.event_tag.model import EventTag
from pmapi.event_artist.model import EventDateArtist
from pmapi.event_date.model import EventDateTicket

from pmapi.event.model import Event, user_event_following_table

from .model import EventDate, user_event_date_interested_table, user_event_date_going_table

from pmapi.utils import normalize_bounds

from pmapi import exceptions as exc

import pmapi.media_item.controllers as media_items
from pmapi.hcaptcha.controllers import validate_hcaptcha

# from dateutil.relativedelta import *
from dateutil.rrule import rrule, MO, TU, WE, TH, FR, SA, SU, YEARLY, MONTHLY, WEEKLY
from dateutil import tz

import time

Activity = activity_plugin.activity_cls


def get_event_date_or_404(id):
    event_date = get_event_date(id)
    if not event_date:
        msg = "No such event_date with id {}".format(id)
        raise exc.RecordNotFound(msg)
    return event_date


def get_event_date(id):
    # apply interested/going expression if user logged in

    going_expression = (
        db.session.query(user_event_date_going_table)
        .filter(
            and_(
                user_event_date_going_table.c.user_id == current_user.id,
                user_event_date_going_table.c.event_date_id == EventDate.id,
            )
        )
        .exists()
    )

    interested_expression = (
        db.session.query(user_event_date_interested_table)
        .filter(
            and_(
                user_event_date_interested_table.c.user_id == current_user.id,
                user_event_date_interested_table.c.event_date_id == EventDate.id,
            )
        )
        .exists()
    )

    query = EventDate.query

    if current_user.is_authenticated:
        query = query.options(with_expression(
            EventDate.user_interested,
            interested_expression,
        ),
            with_expression(
            EventDate.user_going,
            going_expression,
        ))

    return query.get(id)


def add_event_date_with_datetime(
    event,
    date_time,
    location,
    description=None,
    description_attribute=None,
    url=None,
    ticket_url=None,
    size=None,
    artists=None,
    creator=None,
):
    # this function is used by the post eventdate endpoint
    if date_time:
        if date_time.get("start", None) is None:
            raise exc.InvalidAPIRequest("Start date required")
        start = datetime.strptime(date_time["start"], "%Y-%m-%d %H:%M:%S").replace(
            second=0, microsecond=0
        )
        start_naive = start.replace(tzinfo=None)

        if date_time.get("end", None) is None:
            end = start
        end = datetime.strptime(date_time["end"], "%Y-%m-%d %H:%M:%S").replace(
            second=0, microsecond=0
        )
        end_naive = end.replace(tzinfo=None)

        # trigger new reivison of event
        event.updated_at = datetime.utcnow()

        event_date = add_event_date(
            event=event,
            start_naive=start_naive,
            end_naive=end_naive,
            location=location,
            description=description,
            description_attribute=description_attribute,
            size=size,
            url=url,
            ticket_url=ticket_url,
            artists=artists,
        )


        db.session.commit()


        return event

    else:

        raise exc.InvalidAPIRequest(
            "date_time required for making healthy computer program"
        )


def add_event_date(
    start_naive,
    end_naive,
    event,
    location=None,  # this parameter is used by add_event_date_with_datetime
    event_location=None,  # this parameter is add_event_date_with_datetime
    creator=None,
    tz=None,
    url=None,
    ticket_url=None,
    description=None,
    description_attribute=None,
    size=None,
    artists=None,
    lineup_images=None,
    activity=True,
    date_confirmed=True,
):
    """accepts naive start and end dates and derives timezone from location
    if it not provided"""

    if not event_location:
        # get EventLocation from location object place_id
        if not location:
            raise exc.InvalidAPIRequest("Location required")
        event_location = event_locations.get_location(location["place_id"])
        if not event_location:
            event_location = event_locations.add_new_event_location(
                creator=creator, **location
            )
    if tz:
        tz_obj = pytz.timezone(tz)
    else:
        tf = TimezoneFinder()
        tz = tf.timezone_at(lng=event_location.lng, lat=event_location.lat)
        tz_obj = pytz.timezone(tz)

    if not start_naive:
        raise exc.InvalidAPIRequest("Start date/time required")

    if not end_naive:
        end_naive = start_naive

    if end_naive < start_naive:
        raise exc.InvalidAPIRequest(
            "End date/time can't be before the start date/time")

    start_utc = tz_obj.localize(start_naive)
    start_utc = start_utc.astimezone(pytz.utc)
    start_utc = start_utc.replace(
        tzinfo=None
    )  # strip tz info before adding to db. very important!
    end_utc = tz_obj.localize(end_naive)
    end_utc = end_utc.astimezone(pytz.utc)
    end_utc = end_utc.replace(
        tzinfo=None
    )  # strip tz info before adding to db. very important!


    event_date = EventDate(
        event=event,
        start_naive=start_naive,
        end_naive=end_naive,
        end=end_utc,
        start=start_utc,
        tz=tz,
        location=event_location,
        description=description,
        description_attribute=description_attribute,
        size=size,
        url=url,
        date_confirmed=date_confirmed
    )
    db.session.add(event_date)
    event_date.after_commit = True

    db.session.flush()

    if ticket_url:
        ed_ticket = EventDateTicket(url=ticket_url, event_date=event_date, event=event_date.event)
        db.session.add(ed_ticket)

    if activity:
        activity = Activity(verb=u"create", object=event_date,
                            target=event_date.event)
        db.session.add(activity)

    if artists is not None:
        add_artists_to_date(event_date, artists)

    if lineup_images is not None:
        media_items.add_lineup_images_to_event_date(
            lineup_images, event, event_date)

    
    return event_date


def update_event_date(id, **kwargs):
    event_date = get_event_date_or_404(id)

    date_time = kwargs.get("date_time", None)
    location = kwargs.get("location", None)

    if date_time:
        # location required for timezone info
        if location:
            lat = location["geometry"]["location"]["lat"]
            lng = location["geometry"]["location"]["lng"]
        else:
            lat = event_date.location.lat
            lng = event_date.location.lng

        if date_time.get("start", None) is None:
            raise exc.InvalidAPIRequest("Start date required")
        start_naive = datetime.strptime(
            date_time["start"], "%Y-%m-%d %H:%M:%S")
        start_naive = start_naive.replace(tzinfo=None, second=0, microsecond=0)

        if date_time.get("end", None) is None:
            end_naive = start_naive
        end_naive = datetime.strptime(date_time["end"], "%Y-%m-%d %H:%M:%S")
        end_naive = end_naive.replace(tzinfo=None, second=0, microsecond=0)

        if end_naive < start_naive:
            raise exc.InvalidAPIRequest(
                "End time can't be before the start time")

        try:
            # ADD CORRECT TIMEZONE TO DATE TIME AND THEN CONVERT TO UTC
            tf = TimezoneFinder()
            tz = tf.timezone_at(lng=lng, lat=lat)
            tz_obj = pytz.timezone(tz)

        except UnknownTimeZoneError:
            print("TIMEZONE ERROR")
            pass  # {handle error}

        """
        Date should be received as a naive date
        ie. the local time where the event is happening with no tz info.
        """
        start = start_naive.replace(tzinfo=None)
        start = tz_obj.localize(start)
        start = start.astimezone(pytz.utc)
        start = start.replace(tzinfo=None)
        end = end_naive.replace(tzinfo=None)
        end = tz_obj.localize(end_naive)
        end = end.astimezone(pytz.utc)
        end = end.replace(tzinfo=None)

        event_date.start = start
        event_date.end = end
        event_date.start_naive = start_naive
        event_date.end_naive = end_naive
        event_date.tz = tz
        event_date.date_confirmed = True

    if location:
        lat = location["geometry"]["location"]["lat"]
        lng = location["geometry"]["location"]["lng"]

        try:
            # ADD CORRECT TIMEZONE TO DATE TIME AND THEN CONVERT TO UTC
            tf = TimezoneFinder()
            tz = tf.timezone_at(lng=lng, lat=lat)
            tz_obj = pytz.timezone(tz)

        except UnknownTimeZoneError:
            print("TIMEZONE ERROR")
            pass  # {handle error}

        event_location_creator = current_user

        event_location = event_locations.add_new_event_location(
            event_location_creator, **location
        )
        event_date.location = event_location
        event_date.tz = tz
        db.session.flush()
        activity = Activity(verb=u"update", object=event_date.location,
                            target=event_date)
        db.session.add(activity)
        # date settings not touched
        # update location of all future eventdates

    if "cancelled" in kwargs:
        event_date.cancelled = kwargs.pop("cancelled")

    if "description" in kwargs:
        event_date.description = kwargs.pop("description", None)

    if "description_attribute" in kwargs:
        event_date.description_attribute = kwargs.pop(
            "description_attribute", None)

    if "url" in kwargs:
        event_date.url = kwargs.pop("url")

    if "tickets" in kwargs:
        # delete all previous tickets
        for ticket in event_date.tickets:
            db.session.delete(ticket)

        # set new ticket urls
        tickets = kwargs.pop("tickets")
        for ticket in tickets:
            ed_ticket = EventDateTicket(
                url=ticket["url"], description=ticket["description"], price_min=ticket["price_min"], price_max=ticket["price_max"], price_currency_code=ticket["price_currency_code"], event_date=event_date, event=event_date.event)
            db.session.add(ed_ticket)
    
    if "ticket_url" in kwargs:
        ed_ticket = EventDateTicket(url=kwargs.pop("ticket_url"), event_date=event_date, event=event_date.event)
        db.session.add(ed_ticket)

    if "size" in kwargs:
        event_date.size = kwargs.pop("size")

    if "remove_artists" in kwargs:
        remove_artists_from_date(
            event_date, kwargs.pop("remove_artists"))

    if "add_artists" in kwargs:
        add_artists_to_date(
            event_date, kwargs.pop("add_artists"))

    if "update_artists" in kwargs:
        update_artists_of_date(
            event_date, kwargs.pop("update_artists"))

    if "lineup_images" in kwargs:
        media_items.add_lineup_images_to_event_date(kwargs.pop(
            "lineup_images"), event_date.event, event_date, creator=current_user)

    if "media_items" in kwargs:
        media_items.add_media_to_event(kwargs.pop(
            "media_items"), event_date.event, event_date, creator=current_user)

    # this field is useful for triggering
    # a new version of the parent event object in continuum
    event_date.event.updated_at = datetime.utcnow()

    db.session.flush()
    activity = Activity(verb=u"update", object=event_date,
                        target=event_date.event)
    db.session.add(activity)
    # create_notification('UPDATE EVENT', activity, ed.event.followers)
    
    if "description" in kwargs:
        event_date.after_commit = True

    db.session.commit()

    return event_date


def delete_future_event_dates(event, preserve_next=False, activity=True):
    event_dates = event.future_event_dates
    if preserve_next:
        # don't delete the next event date
        # used when disabling rrule
        event_dates = event.future_event_dates_except_next

    for ed in event_dates:
        db.session.delete(ed)
        db.session.flush()
        if activity:
            activity = Activity(verb=u"delete", object=ed, target=event)
            db.session.add(activity)

# DONT USE THIS METHOD FOR AUTOGENERATION (BECAUSE DATE_CONFIRMED WILL BE SET TO TRUE IN CASES WHERE IT SHOULD NOT BE)


def generate_future_event_dates(
    event,
    date_time=None,
    event_location=None,
    rrule=None,
    url=None,
    next_event_date_description=None,
    next_event_date_description_attribute=None,
    next_event_date_size=None,
    next_event_date_artists=None,
    next_event_date_lineup_images=None,
    activity=True,
):

    if rrule is None and event.rrule:
        # use existing rrule if one not provided
        rrule = event.rrule

    if event_location is None and rrule:
        event_location = rrule.default_location

    if date_time:
        if date_time.get("start", None) is None:
            raise exc.InvalidAPIRequest("Start date required")
        start_naive = datetime.strptime(
            date_time["start"], "%Y-%m-%d %H:%M:%S")
        start_naive = start_naive.replace(tzinfo=None, second=0, microsecond=0)

        if date_time.get("end", None) is None:
            end_naive = start_naive
        end_naive = datetime.strptime(date_time["end"], "%Y-%m-%d %H:%M:%S")
        end_naive = end_naive.replace(tzinfo=None, second=0, microsecond=0)

        # Find timezone info
        try:
            tf = TimezoneFinder()
            tz = tf.timezone_at(lng=event_location.lng, lat=event_location.lat)

        except UnknownTimeZoneError:
            print("TIMEZONE ERROR")

    else:
        # if dateTime not provided,
        # work something out to generate new event dates from
        start_naive = event.last_event_date().start_naive
        end_naive = event.last_event_date().end_naive

        tz = event.last_event_date().tz

    if rrule is None or rrule.separation_count == 0:
        # event is a one-off
        event.recurring = False
        add_event_date(
            event=event,
            start_naive=start_naive,
            end_naive=end_naive,
            event_location=event_location,
            tz=tz,
            url=url,
            description=next_event_date_description,
            description_attribute=next_event_date_description_attribute,
            size=next_event_date_size,
            artists=next_event_date_artists,
            lineup_images=next_event_date_lineup_images,
            activity=activity,
        )

    else:

        if url:
            rrule.default_url = url

        else:
            url = rrule.default_url

        # event is recurring
        event.recurring = True
        startdates, enddates = generateRecurringDates(
            rrule, start_naive, end_naive)

        # work out how many dates to generate
        limit = 10 - len(event.future_event_dates)

        if date_time is None:
            limit += 1

        # generate new event dates
        # limit event dates to 10
        # for start, end in zip(startdates[:10], enddates[:10]):
        for index, start_naive in enumerate(startdates[:limit]):
            if date_time is None and index == 0:
                pass
                # if dateTime was not provided, then we are
                # generating future dates without deleting
                # other future dates.
                # index 0 will be the date that we are starting from
                # and we don't want to duplicate it so we skip it.
            else:
                end_naive = None
                try:
                    if enddates[index] is not None:
                        end_naive = enddates[index]
                except IndexError:
                    # print("no enddate")
                    pass

                add_event_date(
                    event=event,
                    start_naive=start_naive,
                    end_naive=end_naive,
                    event_location=event_location,
                    tz=tz,
                    url=url,
                    description=next_event_date_description,
                    description_attribute=next_event_date_description_attribute,
                    size=next_event_date_size,
                    artists=next_event_date_artists,
                    lineup_images=next_event_date_lineup_images,
                    activity=activity,
                    # the first date should be confirmed
                    date_confirmed=True if rrule.exact or index == 0 else False
                )
                # next_event_date_description and artists only used once
                next_event_date_description = None
                next_event_date_artists = None
                next_event_date_description_attribute = None
                next_event_date_lineup_images = None
    return event


# used by events.add_event and events.update_event functions
# to generate a series of dates for an event
# ( should become an automated task in the future )
def generateRecurringDates(rp, start, end=None):

    print(rp)
    days = [MO, TU, WE, TH, FR, SA, SU]

    def getWeekInMonth(date):
        from calendar import Calendar

        cal = Calendar()  # week starts Monday
        # cal = Calendar(6) # week stars Sunday
        weeks = cal.monthdayscalendar(date.year, date.month)
        result = 0
        for x in range(len(weeks)):
            result += 1
            if date.day in weeks[x]:
                return result

        return 1  # return 1 if all else fails

    startdates = []
    enddates = []

    # on leap years, the 29th of March exists
    try:
        two_years_away = start.replace(year=start.year + 2)
    except ValueError:
        if (start.month == 2 and start.day == 29 and  # leap day
                isleap(start.year)):
            two_years_away = start.replace(year=start.year + 2, day=28)
        else:
            raise

    try:
        ten_years_away = start.replace(year=start.year + 10)
    except ValueError:
        if (start.month == 2 and start.day == 29 and  # leap day
                isleap(start.year)):
            ten_years_away = start.replace(year=start.year + 10, day=28)
        else:
            raise

    start_weekday = start.weekday()
    start_day = start.day
    start_month = start.month
    start_week_of_month = getWeekInMonth(start)

    duration = end - start

    if rp.recurring_type == 1:
        # weekly
        startdates = list(
            rrule(
                freq=WEEKLY,
                interval=rp.separation_count,
                byweekday=start_weekday,
                dtstart=start,
                until=two_years_away,
            )
        )

    elif rp.recurring_type == 2:
        # monthly
        if rp.week_of_month:
            startdates = list(
                rrule(
                    MONTHLY,
                    interval=rp.separation_count,
                    byweekday=days[start_weekday](start_week_of_month),
                    dtstart=start,
                    until=ten_years_away,
                )
            )

        else:
            # absolute monthlhy date
            startdates = list(
                rrule(
                    MONTHLY,
                    interval=rp.separation_count,
                    bymonthday=start_day,
                    dtstart=start,
                    until=ten_years_away,
                )
            )

    elif rp.recurring_type == 3:
        # yearly
        if rp.week_of_month:
            startdates = list(
                rrule(
                    YEARLY,
                    interval=rp.separation_count,
                    bymonth=start_month,
                    byweekday=days[start_weekday](start_week_of_month),
                    dtstart=start,
                    until=ten_years_away,
                )
            )

        else:
            # absolute day of month of year
            startdates = list(
                rrule(
                    YEARLY,
                    interval=rp.separation_count,
                    bymonth=start_month,
                    bymonthday=start_day,
                    dtstart=start,
                    until=ten_years_away,
                )
            )


    else:
        raise exc.InvalidAPIRequest("Invalid recurring_type (1-3)")

    for date in startdates:
        enddates.append(date + duration)

    return startdates, enddates


def delete_event_date(id):
    event_date = get_event_date_or_404(id)
    event = event_date.event
    # this field is useful for triggering
    # a new version of the parent event object in continuum
    event.updated_at = datetime.utcnow()
    db.session.delete(event_date)
    db.session.flush()
    activity = Activity(verb=u"delete", object=event_date,
                        target=event_date.event)
    db.session.add(activity)
    db.session.commit()
    return event

"""
def query_event_dates(**kwargs):

    # Base query
    query = db.session.query(EventDate).join(Event, EventDate.event_id == Event.id)
    location_filters = kwargs.get("location", None)
    bounds = kwargs.get("bounds", None)
    lat, lng = None, None
    radius = kwargs.get("radius", None)
    sort_option = kwargs.get("sort_option", None)

    distance_expression = None
    
    # Distance filter if location is provided
    if location_filters:
        lat = float(location_filters["lat"])
        lng = float(location_filters["lng"])
        if lat is None or lng is None:
            raise exc.InvalidAPIRequest("lat and lng are required for nearby search.")

        distance_expression = func.ST_Distance(
            cast(EventLocation.geo, Geography(srid=4326)),
            cast(f"SRID=4326;POINT({lng} {lat})", Geography(srid=4326)),
        )

        query = (
            query.join(EventLocation, EventDate.location_id == EventLocation.id)
                 .add_columns(distance_expression.label("distance"))
        )

        # Apply radius filter
        if radius:
            query = query.filter(distance_expression <= radius)

    elif bounds:
        # Bounds filter
        northEast = bounds["_northEast"]
        southWest = bounds["_southWest"]

        bbox = func.ST_MakeEnvelope(
            southWest["lng"], southWest["lat"], northEast["lng"], northEast["lat"], 4326
        )

        query = query.join(EventLocation, EventDate.location_id == EventLocation.id)
        query = query.filter(func.ST_Intersects(EventLocation.geo, bbox))

    # User-related filters
    if current_user.is_authenticated:
        query = query.options(
            with_expression(
                EventDate.user_interested,
                db.session.query(user_event_date_interested_table)
                    .filter(
                        user_event_date_interested_table.c.user_id == current_user.id,
                        user_event_date_interested_table.c.event_date_id == EventDate.id,
                    )
                    .exists(),
            ),
            with_expression(
                EventDate.user_going,
                db.session.query(user_event_date_going_table)
                    .filter(
                        user_event_date_going_table.c.user_id == current_user.id,
                        user_event_date_going_table.c.event_date_id == EventDate.id,
                    )
                    .exists(),
            ),
        )

    # Date filters
    if date_min := kwargs.get("date_min"):
        query = query.filter(EventDate.end >= date_min)
    if date_max := kwargs.get("date_max"):
        query = query.filter(
            and_(
                or_(EventDate.end <= date_max, EventDate.end.is_(None)),
                EventDate.start <= date_max,
            )
        )

    # Tag filters
    if tags := kwargs.get("tags"):
        query = query.filter(Event.event_tags.any(EventTag.tag_id.in_(tags)))


    # Sort and distinct logic
    if kwargs.get("distinct"):
        row_number_column = func.row_number().over(
            partition_by=EventDate.event_id, order_by=EventDate.start.asc()
        ).label("row_number")
        subquery = query.add_column(row_number_column).add_column(distance_expression).subquery()
        query = db.session.query(aliased(EventDate, subquery)).filter(subquery.c.row_number == 1)
    print(query.all())

    if sort_option == "distance" and distance_expression:
        query = query.order_by(func.coalesce(subquery.c.distance, 0).asc(), EventDate.start.asc())
    else:
        query = query.order_by(EventDate.start.asc())


    # Paginate results
    results = paginated_results(EventDate, query, **kwargs)

    # Enrich first page with top artists/tags/regions
    if kwargs.get("page", 1) == 1:
        enrich_results_with_top_entities(results, query)

    return results
"""
"""
mostly working just not distance query expresssion
def query_event_dates(**kwargs):
    # Base query
    query = db.session.query(EventDate).join(Event, EventDate.event_id == Event.id)
    location_filters = kwargs.get("location", None)
    bounds = kwargs.get("bounds", None)
    lat, lng = None, None
    radius = kwargs.get("radius", None)
    sort_option = kwargs.get("sort_option", None)
    # Create an alias for EventDate that we'll use throughout
    EventDateAlias = aliased(EventDate)
    EventDateSubAlias = None
    query = db.session.query(EventDateAlias)
    
    # Distance filter if location is provided
    if location_filters:
        lat = float(location_filters["lat"])
        lng = float(location_filters["lng"])
        if lat is None or lng is None:
            raise exc.InvalidAPIRequest("lat and lng are required for nearby search.")

        distance_expression = func.ST_Distance(
            cast(EventLocation.geo, Geography(srid=4326)),
            cast(f"SRID=4326;POINT({lng} {lat})", Geography(srid=4326)),
        )

        query = (
            query.join(EventLocation, EventDateAlias.location_id == EventLocation.id)
            .join(Event, EventDateAlias.event_id == Event.id)
            .options(with_expression(EventDateAlias.distance, distance_expression))
        )

        # Apply radius filter
        if radius:
            query = query.filter(distance_expression <= radius)

    if bounds:

        # Bounds filter
        northEast = bounds["_northEast"]
        southWest = bounds["_southWest"]

        bbox = func.ST_MakeEnvelope(
            southWest["lng"], southWest["lat"], northEast["lng"], northEast["lat"], 4326
        )

        query = (
            query
            .filter(func.ST_Intersects(EventLocation.geo, bbox))
        )

    # User-related filters
    if current_user.is_authenticated:
        query = query.options(
            with_expression(
                EventDateAlias.user_interested,
                db.session.query(user_event_date_interested_table)
                    .filter(
                        user_event_date_interested_table.c.user_id == current_user.id,
                        user_event_date_interested_table.c.event_date_id == EventDateAlias.id,
                    )
                    .exists(),
            ),
            with_expression(
                EventDateAlias.user_going,
                db.session.query(user_event_date_going_table)
                    .filter(
                        user_event_date_going_table.c.user_id == current_user.id,
                        user_event_date_going_table.c.event_date_id == EventDateAlias.id,
                    )
                    .exists(),
            ),
        )

    # Date filters
    if date_min := kwargs.get("date_min"):
        query = query.filter(EventDateAlias.end >= date_min)
    if date_max := kwargs.get("date_max"):
        query = query.filter(
            and_(
                or_(EventDateAlias.end <= date_max, EventDateAlias.end.is_(None)),
                EventDateAlias.start <= date_max,
            )
        )

    # Tag filters
    if tags := kwargs.get("tags"):
        query = query.filter(Event.event_tags.any(EventTag.tag_id.in_(tags)))

    # Sort and distinct logic
    if kwargs.get("distinct"):
        # Add row_number for distinct filtering
        row_number_column = func.row_number().over(
            partition_by=EventDateAlias.event_id, 
            order_by=EventDateAlias.start.asc()
        ).label("row_number")

        # Create subquery
        subquery = query.add_columns(row_number_column, EventDateAlias.distance).subquery()
        
        # Create new query from subquery using alias
        EventDateSubAlias = aliased(EventDateAlias, subquery)
        query = db.session.query(EventDateSubAlias).filter(
            subquery.c.row_number == 1
        )

    # Sorting logic based on distance or start date
    if sort_option == "distance" and location_filters:
        if EventDateSubAlias:
            query = query.order_by(
                func.coalesce(EventDateSubAlias.distance, 0).asc(), 
                EventDateSubAlias.start.asc()
            )
        else:
            query = query.order_by(
                func.coalesce(EventDateAlias.distance, 0).asc(), 
                EventDateAlias.start.asc()
            )
    else:
        if EventDateSubAlias:
            query = query.order_by(EventDateSubAlias.start.asc())
        else: 
            query = query.order_by(EventDateAlias.start.asc())

    # Paginate results
    results = paginated_results(EventDate, query, **kwargs)

    # Enrich first page with top artists/tags/regions
    if kwargs.get("page", 1) == 1:
        enrich_results_with_top_entities(results, query)

    return results
"""

def query_event_dates(**kwargs):
    # Base query
    query = db.session.query(EventDate).join(Event, EventDate.event_id == Event.id)
    location_filters = kwargs.get("location", None)
    bounds = kwargs.get("bounds", None)
    lat, lng = None, None
    radius = kwargs.get("radius", None)
    country_id = kwargs.get("country_id", None)
    region_name = kwargs.get("region_name", None)

    creator_user = kwargs.get("creator_user", None)
    host_user = kwargs.get("host_user", None)
    interested_user = kwargs.get("interested_user", None)
    going_user = kwargs.get("going_user", None)
    following_user = kwargs.get("following_user", None)
    reviewed_user = kwargs.get("reviewed_user", None)
    all_related_to_user = kwargs.get("all_related_to_user", None)

    empty_lineup = kwargs.get("empty_lineup", None)
    date_unconfirmed = kwargs.get("date_unconfirmed", None)

    sort_option = kwargs.pop("sort", None)
    if sort_option is None:
        sort_option = kwargs.pop('sort_option', None) # deprecate this

    # Create an alias for EventDate that we'll use throughout
    EventDateAlias = aliased(EventDate)

    query = db.session.query(EventDateAlias)
    
    # Initialize distance_expression as None
    distance_expression = None

    # Distance filter if location is provided
    if location_filters and location_filters["lat"] and location_filters["lng"]:
        print('LOCATION FILTERS')
        lat = float(location_filters["lat"])
        lng = float(location_filters["lng"])
        if lat is None or lng is None:
            raise exc.InvalidAPIRequest("lat and lng are required for nearby search.")

        distance_expression = func.ST_Distance(
            cast(EventLocation.geo, Geography(srid=4326)),
            cast(f"SRID=4326;POINT({lng} {lat})", Geography(srid=4326)),
        )

        query = (
            query.join(EventLocation, EventDateAlias.location_id == EventLocation.id)
            .join(Event, EventDateAlias.event_id == Event.id)
            .options(with_expression(EventDateAlias.distance, distance_expression))
        )

        if bounds is None and radius == 0:
            # used on the home page of partyman
            # to return a list of events in proximity of point/users location
            # and return the radius in response
            radii = [
                10000,
                20000,
                50000,
                100000,
                200000,
                500000,
                1000000,
                2000000,
                5000000,
                10000000,
                20000000,
            ]

            # Add row_number for distinct filtering
            row_number_column = func.row_number().over(
                partition_by=EventDateAlias.event_id, 
                order_by=EventDateAlias.start.asc()
            ).label("row_number")

            # Create subquery including all columns from EventDateAlias
            subquery = query.add_columns(row_number_column).subquery()
            
            # Create new query from subquery using alias
            CountEventDateAlias = aliased(EventDate, subquery)
            count_query = db.session.query(CountEventDateAlias).join(EventLocation, CountEventDateAlias.location_id == EventLocation.id).filter(
                subquery.c.row_number == 1
            )

            for r in radii:               
                count = (
                    count_query
                    .filter(
                        func.ST_DWithin(
                            cast(EventLocation.geo, Geography(srid=4326)),
                            cast(
                                "SRID=4326;POINT(%f %f)" % (lng, lat),
                                Geography(srid=4326),
                            ),
                            r,
                        )
                    )
                    .from_self()
                    .count()
                )
                # threshold of events required before trying the next radius
                if count >= 4:
                    radius = r
                    break

        # Apply radius filter
        if radius:
            query = query.filter(distance_expression <= radius)

    # location not provided
    else:
        query = query.join(EventLocation, EventDateAlias.location_id == EventLocation.id)
        query = query.join(Event, EventDateAlias.event_id == Event.id)

    if bounds:
        # Ensure EventLocation is joined if not already

        # Bounds filter
        northEast = bounds["_northEast"]
        southWest = bounds["_southWest"]

        bbox = func.ST_MakeEnvelope(
            southWest["lng"], southWest["lat"], northEast["lng"], northEast["lat"], 4326
        )

        query = query.filter(func.ST_Intersects(EventLocation.geo, bbox))

    if country_id:
        query = query.filter(EventLocation.country_id == country_id)

    if region_name:
        query = query.join(Region, EventLocation.region_id == Region.id)
        query = query.filter(Region.long_name == region_name)

    # Date filters
    if date_min := kwargs.get("date_min"):
        query = query.filter(EventDateAlias.end >= date_min)
    if date_max := kwargs.get("date_max"):
        query = query.filter(
            and_(
                or_(EventDateAlias.end <= date_max, EventDateAlias.end.is_(None)),
                EventDateAlias.start <= date_max,
            )
        )

    # Tag filters
    if tags := kwargs.get("tags"):
        query = query.filter(Event.event_tags.any(EventTag.tag_id.in_(tags)))

    if empty_lineup:
        query = query.filter(
                ~EventDateAlias.artists.any()
            )
        
    if date_unconfirmed:
        query = query.filter(
                EventDateAlias.date_confirmed == False
            )

    # Filter hidden events out
    query = query.filter(
        or_(
                    Event.hidden == False,
                    and_(
                        Event.hidden == True,
                        Event.creator_id is not None, 
                        Event.creator_id == current_user.id
                    )
                ))

    # User related filters
    if creator_user:
        user = users.get_user_or_404(creator_user)
        query = query.filter(Event.creator_id == user.id)

    if host_user:
        user = users.get_user_or_404(host_user)
        query = query.filter(Event.host_id == user.id)

    if interested_user:
        user = users.get_user_or_404(interested_user)
        interested_event_date_ids = db.session.query(
            user_event_date_interested_table.c.event_date_id).filter(user_event_date_interested_table.c.user_id == user.id)
        query = query.filter(
            EventDateAlias.id.in_(interested_event_date_ids)
        )

    if going_user:
        user = users.get_user_or_404(going_user)
        going_event_date_ids = db.session.query(
            user_event_date_going_table.c.event_date_id).filter(user_event_date_going_table.c.user_id == user.id)
        query = query.filter(
            EventDateAlias.id.in_(going_event_date_ids)
        )

    if reviewed_user:
        user = users.get_user_or_404(reviewed_user)
        query = query.join(EventReview, EventDateAlias.event_id == EventReview.event_id)
        query = query.filter(EventReview.creator_id == user.id)

    if following_user:
        user = users.get_user_or_404(following_user)
        following_event_ids = db.session.query(
            user_event_following_table.c.event_id).filter(user_event_date_going_table.c.user_id == user.id)
        query = query.filter(
            Event.id.in_(following_event_ids)
        )

    if all_related_to_user:
        user = users.get_user_or_404(all_related_to_user)
        query = query.outerjoin(EventReview, EventDateAlias.event_id == EventReview.event_id)
        interested_event_date_ids = db.session.query(
            user_event_date_interested_table.c.event_date_id).filter(user_event_date_interested_table.c.user_id == user.id)
        going_event_date_ids = db.session.query(
            user_event_date_going_table.c.event_date_id).filter(user_event_date_going_table.c.user_id == user.id)
        following_event_ids = db.session.query(
            user_event_following_table.c.event_id).filter(user_event_date_going_table.c.user_id == user.id)
        query = query.filter(
            or_(
                (EventReview.creator_id == user.id),
                (Event.creator_id == user.id), (Event.host_id == user.id),
                (EventDateAlias.id.in_(going_event_date_ids)),
                (EventDateAlias.id.in_(interested_event_date_ids)), (
                    Event.id.in_(following_event_ids)
                ))
        )

    # Apply going/interested expression to results
    if current_user.is_authenticated:
        query = query.options(
            with_expression(
                EventDateAlias.user_interested,
                db.session.query(user_event_date_interested_table)
                    .filter(
                        user_event_date_interested_table.c.user_id == current_user.id,
                        user_event_date_interested_table.c.event_date_id == EventDateAlias.id,
                    )
                    .exists(),
            ),
            with_expression(
                EventDateAlias.user_going,
                db.session.query(user_event_date_going_table)
                    .filter(
                        user_event_date_going_table.c.user_id == current_user.id,
                        user_event_date_going_table.c.event_date_id == EventDateAlias.id,
                    )
                    .exists(),
            ),
        )


    # Sort and distinct logic
    if kwargs.get("distinct"):
        # Add row_number for distinct filtering
        row_number_column = func.row_number().over(
            partition_by=EventDateAlias.event_id, 
            order_by=EventDateAlias.start.asc()
        ).label("row_number")

        # Create subquery including all columns from EventDateAlias
        subquery = query.add_columns(row_number_column).subquery()
        
        # Create new query from subquery using alias
        EventDateAlias = aliased(EventDate, subquery)
        query = db.session.query(EventDateAlias).filter(
            subquery.c.row_number == 1
        )
        
        # Reapply the distance expression if it exists
        if distance_expression is not None:
            query = query.join(EventLocation, EventDateAlias.location_id == EventLocation.id)
            query = query.options(with_expression(
                EventDateAlias.distance,
                distance_expression
            ))

    # Sorting logic based on distance or start date
    if sort_option == "distance" and location_filters:
        query = query.order_by(
            func.coalesce(EventDateAlias.distance, 0).asc(), 
            EventDateAlias.start.asc()
        )
    elif sort_option:
        if sort_option == 'date':
            sort_option = 'start' # deprecate this

        desc = kwargs.pop('desc', False)
        sort_field = getattr(EventDateAlias, sort_option)
        if sort_field and desc:
            from sqlalchemy import desc
            sort_field = desc(sort_field)
        query = query.order_by(sort_field)
    else:
        desc = kwargs.pop('desc', False)
        sort_field = getattr(EventDateAlias, 'start')
        if desc:
            from sqlalchemy import desc
            sort_field = desc(sort_field)
        query = query.order_by(sort_field)

    # Paginate results
    results = paginated_results(EventDate, query, **kwargs)

    results.radius = radius

    # Enrich first page with top artists/tags/regions
    if kwargs.get("page", 1) == 1:
        enrich_results_with_top_entities(results, query)

    return results


def enrich_results_with_top_entities(results, query):
    artists, tags, regions = [], [], []

    for ed in query.slice(0, 100).all():
        for artist in ed.artists:
            artists.append(artist)
        for tag in ed.event.event_tags:
            tags.append(tag)
        region = ed.location.region
        if (hasattr(region, 'id')):
            region.lat =  ed.location.lat
            region.lng = ed.location.lng
            regions.append(region)

    results.top_artists = get_top_entities(artists, "artist_id", 10)
    results.top_tags = get_top_entities(tags, "tag_id", 20)
    results.top_regions = get_top_entities(regions, "id", 20)


def get_top_entities(entities, id_attr, limit):
    valid_entities = [e for e in entities if e is not None and hasattr(e, id_attr)]
    counter = Counter(getattr(e, id_attr) for e in valid_entities)
    unique_entities = list({getattr(e, id_attr): e for e in valid_entities}.values())
    return sorted(unique_entities, key=lambda e: counter[getattr(e, id_attr)], reverse=True)[:limit]


"""
def query_event_dates(**kwargs):

    # for nearby search
    lat = None
    lng = None
    distance_expression = None
    sort_option = kwargs.get("sort_option", None)
    radius = kwargs.get("radius", None)
    bounds = kwargs.get("bounds", None)

    seconds_start = time.time()

    going_expression = (
        db.session.query(user_event_date_going_table)
        .filter(
            and_(
                user_event_date_going_table.c.user_id == current_user.id,
                user_event_date_going_table.c.event_date_id == EventDate.id,
            )
        )
        .exists()
    )

    interested_expression = (
        db.session.query(user_event_date_interested_table)
        .filter(
            and_(
                user_event_date_interested_table.c.user_id == current_user.id,
                user_event_date_interested_table.c.event_date_id == EventDate.id,
            )
        )
        .exists()
    )


    if kwargs.get("location", None) is not None:
        location = kwargs.get("location")
        lat = float(location["lat"])
        lng = float(location["lng"])

        if lat is None or lng is None:
            raise exc.InvalidAPIRequest(
                "lat and lng are required for nearby search.")

        distance_expression = func.ST_Distance(
            cast(EventLocation.geo, Geography(srid=4326)),
            cast("SRID=4326;POINT(%f %f)" % (lng, lat), Geography(srid=4326)),
        )

        query = (
            db.session.query(EventDate)
            .populate_existing()
            .options(
                with_expression(
                    EventDate.distance,
                    distance_expression,
                ),
            )
            .join(Event, EventDate.event_id == Event.id)
            .join(EventLocation, EventDate.location_id == EventLocation.id)
        )

    else:
        query = db.session.query(EventDate)
        query = query.join(Event)

    # apply interested/going expression if user logged in
    if current_user.is_authenticated:
        query = query.options(with_expression(
            EventDate.user_interested,
            interested_expression,
        ),
            with_expression(
            EventDate.user_going,
            going_expression,
        ))


    joined_tables = [entity.entity for entity in query._compile_state()._join_entities]

    if EventLocation not in joined_tables:
        query = query.join(EventLocation)

    # add row number column so we can filter
    # for the next occurance of an event date below
    row_number_column = (
        func.row_number()
        .over(partition_by=EventDate.event_id, order_by=asc(EventDate.start))
        .label("row_number")
    )
    query = query.add_column(row_number_column)

    # filter hidden events out
    query = query.filter(
        or_(
                    Event.hidden == False,
                    Event.hidden == True and Event.creator_id == user.id,
                ))


    if kwargs.get("creator_user", None) is not None:
        user = users.get_user_or_404(kwargs.pop("creator_user"))
        query = query.filter(Event.creator_id == user.id)

    if kwargs.get("host_user", None) is not None:
        user = users.get_user_or_404(kwargs.pop("host_user"))
        query = query.filter(Event.host_id == user.id)

    if kwargs.get("interested_user", None) is not None:
        user = users.get_user_or_404(kwargs.pop("interested_user"))

        interested_event_date_ids = db.session.query(
            user_event_date_interested_table.c.event_date_id).filter(user_event_date_interested_table.c.user_id == user.id)

        query = query.filter(
            EventDate.id.in_(interested_event_date_ids)
        )

    if kwargs.get("going_user", None) is not None:
        user = users.get_user_or_404(kwargs.pop("going_user"))

        going_event_date_ids = db.session.query(
            user_event_date_going_table.c.event_date_id).filter(user_event_date_going_table.c.user_id == user.id)

        query = query.filter(
            EventDate.id.in_(going_event_date_ids)
        )

    if kwargs.get("following_user", None) is not None:
        user = users.get_user_or_404(kwargs.pop("following_user"))

        following_event_ids = db.session.query(
            user_event_following_table.c.event_id).filter(user_event_date_going_table.c.user_id == user.id)

        query = query.filter(
            Event.id.in_(following_event_ids)
        )

    if kwargs.get("all_related_to_user", None) is not None:
        user = users.get_user_or_404(kwargs.pop("all_related_to_user"))

        interested_event_date_ids = db.session.query(
            user_event_date_interested_table.c.event_date_id).filter(user_event_date_interested_table.c.user_id == user.id)

        going_event_date_ids = db.session.query(
            user_event_date_going_table.c.event_date_id).filter(user_event_date_going_table.c.user_id == user.id)

        following_event_ids = db.session.query(
            user_event_following_table.c.event_id).filter(user_event_date_going_table.c.user_id == user.id)

        query = query.filter(
            or_(
                (Event.creator_id == user.id), (Event.host_id == user.id),
                (EventDate.id.in_(going_event_date_ids)),
                (EventDate.id.in_(interested_event_date_ids)), (
                    Event.id.in_(following_event_ids)
                ))
        )

    if kwargs.get("date_min", None) is not None:
        query = query.filter(EventDate.end >= kwargs.pop("date_min"))

    if kwargs.get("date_max", None) is not None:
        date_max = kwargs.pop("date_max")
        query = query.filter(
            and_(
                or_(
                    EventDate.end <= date_max,
                    EventDate.end.is_(None),
                ),
                EventDate.start <= date_max,
            )
        )

    if kwargs.get("tags", None) is not None:
        tags = kwargs.pop("tags")
        for tag in tags:
            query = query.filter(Event.event_tags.any(EventTag.tag_id == tag))


    if "artists" in kwargs:
        artists = kwargs.pop("artists")
        for artist_id in artists:
            query = query.filter(
                EventDate.artists.any(EventDateArtist.artist_id == artist_id)
            )


    if kwargs.get("duration_options", None) is not None:
        duration_options = kwargs.pop("duration_options")
        search_args = [EventDate.duration ==
                       option for option in duration_options]
        query = query.filter(or_(*search_args))

    if kwargs.get("size_options", None) is not None:
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

    if kwargs.get("locality_id", None) is not None:
        query = query.filter(EventLocation.locality_id ==
                             kwargs.pop("locality_id"))
    if kwargs.get("region_id", None) is not None:
        query = query.filter(EventLocation.region_id ==
                             kwargs.pop("region_id"))
    if kwargs.get("country_id", None) is not None:
        query = query.filter(EventLocation.country_id ==
                             kwargs.pop("country_id"))

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



    # filter event dates within bounds
    if bounds:
        ""
        normalized_bounds = normalize_bounds(bounds)
        northEast = normalized_bounds["_northEast"]
        southWest = normalized_bounds["_southWest"]
        ""
        northEast = bounds["_northEast"]
        southWest = bounds["_southWest"]

        # Create a PostGIS geometry from the bounding box
        bbox = func.ST_MakeEnvelope(
            southWest["lng"], southWest["lat"],
            northEast["lng"], northEast["lat"],
            4326  # SRID for WGS84
        )

        # Handle antimeridian crossing (disabled as this is better handeld on frontend)
        if southWest["lng"] > northEast["lng"] and False:
            # Split the query into two parts
            query = query.filter(
                or_(
                    func.ST_Intersects(
                        func.ST_SetSRID(func.ST_MakePoint(EventLocation.lng, EventLocation.lat), 4326),
                        func.ST_MakeEnvelope(southWest["lng"], southWest["lat"], 180, northEast["lat"], 4326)
                    ),
                    func.ST_Intersects(
                        func.ST_SetSRID(func.ST_MakePoint(EventLocation.lng, EventLocation.lat), 4326),
                        func.ST_MakeEnvelope(-180, southWest["lat"], northEast["lng"], northEast["lat"], 4326)
                    )
                )
            )
        else:
            # Normal case (no antimeridian crossing)
            query = query.filter(
                func.ST_Intersects(
                    func.ST_SetSRID(func.ST_MakePoint(EventLocation.lng, EventLocation.lat), 4326),
                    bbox
                )
            )

    if lat and lng and bounds is None:
        # nearby search
        # 1km -> 00km
        if radius is None:
            # determine best radius
            radii = [
                10000,
                20000,
                50000,
                100000,
                200000,
                500000,
                1000000,
                2000000,
                5000000,
                10000000,
                20000000,
            ]
            for r in radii:
                count = (
                    query.filter(
                        func.ST_DWithin(
                            cast(EventLocation.geo, Geography(srid=4326)),
                            cast(
                                "SRID=4326;POINT(%f %f)" % (lng, lat),
                                Geography(srid=4326),
                            ),
                            r,
                        )
                    )
                    .from_self()
                    .filter(row_number_column == 1)
                    .count()
                    # only count first occurance of event
                )

                # threshold of events required before trying the next radius
                if count >= 4:
                    radius = r
                    query = query.filter(
                        func.ST_DWithin(
                            cast(EventLocation.geo, Geography(srid=4326)),
                            cast(
                                "SRID=4326;POINT(%f %f)" % (lng, lat),
                                Geography(srid=4326),
                            ),
                            r,
                        )
                    )
                    break
        else:
            # use requested radius
            query = query.filter(
                func.ST_DWithin(
                    cast(EventLocation.geo, Geography(srid=4326)),
                    cast(
                        "SRID=4326;POINT(%f %f)" % (lng, lat),
                        Geography(srid=4326),
                    ),
                    radius,
                )
            )

    if kwargs.get("distinct", None) is True:
        # return only the first event date of an event
        # DEPRECATED as of SQLALCHEMY 1.4 query = query.from_self().filter(row_number_column == 1)
        subquery = query.subquery()
        EventDateAlias = aliased(EventDate, subquery)
        query = (
            db.session.query(EventDateAlias)
            .filter(subquery.c.row_number == 1)  # Reference row_number_column from the subquery
        )

    if kwargs.get("empty_lineup", None) is True:
        query = query.filter(
                ~EventDate.artists.any()
            )
        
    if kwargs.get("date_unconfirmed", None) is True:
        query = query.filter(
                EventDate.date_confirmed == False
            )

    if lat and lng:
        # sort options if distance expression is used
        if sort_option == "distance":
            query = query.order_by(
                distance_expression.asc(), EventDate.start_naive.asc()
            )
        else:
            query = query.order_by(
                EventDate.start_naive.asc(), distance_expression.asc()
            )
    else:
        # simply sort by date if distance expression not used
        query = query.order_by(EventDate.start_naive.asc())


        
    seconds_end = time.time()
    print("query time in seconds: ", seconds_end - seconds_start)

    results = paginated_results(EventDate, query, **kwargs)
    results.radius = radius

    # return top artists and tags with the first page of results
    if kwargs.get('page') == 1:

        artists = []
        tags = []
        regions = []

        for ed in query.slice(0, 100).all():  # avoid perfromance issues
            for artist in ed[0].artists:
                artists.append(artist)
            for tag in ed[0].event.event_tags:
                tags.append(tag)
            region = ExtendedRegionSchema().dump(ed[0].location.region)
            if (region.get('id')):
                region['lat'] =  ed[0].location.lat
                region['lng'] = ed[0].location.lng
                regions.append(region)
            
        # Count the occurrences of each item in the lists
        artist_counter = Counter(artist.artist_id for artist in artists)
        tag_counter = Counter(tag.tag_id for tag in tags)
        region_counter = Counter(region['id'] for region in regions)

        # Create a set to keep track of artists already added to the result
        artists_set = set()
        tags_set = set()
        regions_set = set()

        # Create a new list ordered by the frequency of each artist without duplicates
        ordered_artists = [
            artist
            for artist in artists
            if artist.artist_id not in artists_set and not artists_set.add(artist.artist_id)
        ]

        ordered_tags = [
            tag
            for tag in tags
            if tag.tag_id not in tags_set and not tags_set.add(tag.tag_id)
        ]

        ordered_regions = [
            region
            for region in regions
            if region['id'] not in regions_set and not regions_set.add(region['id'])
        ]

        # Sort the new lists by the frequency of each item
        ordered_artists.sort(
            key=lambda artist: artist_counter[artist.artist_id], reverse=True)
        ordered_tags.sort(
            key=lambda artist: tag_counter[tag.tag_id], reverse=True)
        ordered_regions.sort(
            key=lambda region: region_counter[region['id']], reverse=True)

        seconds_end_2 = time.time()
        print("tag/artist time in seconds: ", seconds_end_2 - seconds_start)

        results.top_artists = ordered_artists[0: 10]
        results.top_tags = ordered_tags[0: 20]
        results.top_regions = ordered_regions[0:20]

    return results
"""

def toggle_going(id):
    event_date = get_event_date_or_404(id)
    user = current_user

    if not user.is_authenticated:
        raise exc.NotAuthenticated()

    # remove from interested table
    if event_date in user.interested_event_dates:
        user.interested_event_dates.remove(event_date)

    # toggle going state
    if event_date not in user.going_event_dates:
        user.going_event_dates.append(event_date)
    else:
        user.going_event_dates.remove(event_date)

    db.session.commit()
    return event_date


def toggle_interested(id):
    event_date = get_event_date_or_404(id)
    user = current_user

    if not user.is_authenticated:
        raise exc.NotAuthenticated()

    # remove from going table
    if event_date in user.going_event_dates:
        user.going_event_dates.remove(event_date)

    if event_date not in user.interested_event_dates:
        user.interested_event_dates.append(event_date)
    else:
        user.interested_event_dates.remove(event_date)

    db.session.commit()
    return event_date


def ics_download(id):
    event_date = get_event_date_or_404(id)
    timezone = tz.gettz(event_date.tz)

    filename = event_date.event.name + \
        ' | ' + event_date.start_naive.strftime("%B %d, %Y")

    event_url = 'https://partymap.com/event/' + \
        str(event_date.event.id) + "?name=" + \
        event_date.event.name.replace(" ", "_")

    iso_start = event_date.start.strftime("%Y%m%dT%H%M%SZ")
    human_start_time = event_date.start_naive.strftime("%a %d %b %I:%M%p ")
    human_end_time = ""
    if event_date.end_naive:
        human_end_time = event_date.end_naive.strftime("%a %d %b %I:%M%p ")

    description = event_url + '\n\n' + 'Start: ' + human_start_time + '\n' + 'End: ' + human_end_time + \
        '\n' + 'Timezone: ' + event_date.tz + '\n\n' + \
        event_date.event.description + '\n\n'

    if event_date.description:
        description = description + ' ' + event_date.description

    cal = icalendarCalendar()
    cal.add('prodid', '-//Partymap//partymap.com//')
    cal.add('version', '2.0')

    organizer = vCalAddress('MAILTO:noreply@partymap.com')
    organizer.params['cn'] = vText('partymap')

    event = icalendarEvent()
    event['organizer'] = organizer

    event.add('uid', iso_start+'/'+str(event_date.id)+'@partymap.com')
    event.add('summary', event_date.event.name)

    event.add('description', description)
    event.add('geo', (event_date.location.lat, event_date.location.lng))
    event.add('location', event_date.location.description)

    event.add('dtstart', event_date.start_naive.astimezone(timezone))
    event.add('dtend', event_date.end_naive.astimezone(timezone))
    event.add('dtstamp', datetime.utcnow())

    cal.add_component(event)

    # reference for below code: https://github.com/N-Coder/vtimezone-examples
    from khal.khalendar.event import create_timezone
    cal.add_component(create_timezone(pytz.timezone(event_date.tz)))

    response = Response(cal.to_ical(), mimetype="text/calendar")

    # add a filename
    response.headers.set(
        "Content-Disposition", "attachment", filename="{0}.ics".format(filename.encode('latin-1', 'ignore').decode('latin-1'))
    )

    return response
