import pytz
from pytz.exceptions import UnknownTimeZoneError
from timezonefinder import TimezoneFinder
from datetime import datetime
from flask_login import current_user
from geoalchemy2 import func, Geography
from sqlalchemy import cast, or_, and_, asc, distinct
from sqlalchemy.orm import with_expression, lazyload

from pmapi.common.controllers import paginated_results
import pmapi.event_location.controllers as event_locations
import pmapi.event_artist.controllers as event_artists
import pmapi.event.controllers as events
from pmapi.extensions import db, activity_plugin
from pmapi.event_location.model import EventLocation
from pmapi.event_tag.model import EventTag
from pmapi.event_artist.model import EventDateArtist

from pmapi.event.model import Event, user_event_favorites_table
from pmapi import exceptions as exc
from .model import EventDate
import pmapi.suggestions.controllers as suggestions
from pmapi.hcaptcha.controllers import validate_hcaptcha

# from dateutil.relativedelta import *
from dateutil.rrule import rrule, MO, TU, WE, TH, FR, SA, SU, YEARLY, MONTHLY, WEEKLY

import time

Activity = activity_plugin.activity_cls


def get_event_date_or_404(id):
    event_date = get_event_date(id)
    if not event_date:
        msg = "No such event_date with id {}".format(id)
        raise exc.RecordNotFound(msg)
    return event_date


def get_event_date(id):
    return EventDate.query.get(id)


def add_event_date_with_datetime(
    event_id,
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
    event = events.get_event_or_404(event_id)

    if date_time:
        if date_time.get("start", None) is None:
            raise exc.InvalidAPIRequest("Start date required")
        start = datetime.strptime(date_time["start"], "%Y-%m-%d %H:%M:%S").replace(
            second=0, microsecond=0
        )
        start_naive = start.replace(tzinfo=None)

        if date_time.get("end", None) is None:
            raise exc.InvalidAPIRequest("End date required")
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

        return event_date

    else:

        raise exc.InvalidAPIRequest(
            "date_time required for making healthy computer program"
        )


def add_event_date(
    start_naive,
    end_naive,
    event,
    location=None,  # this parameter is used by direct api calls to this function
    event_location=None,  # this parameter is only used by generate_event_dates
    creator=None,
    tz=None,
    url=None,
    ticket_url=None,
    description=None,
    description_attribute=None,
    size=None,
    artists=None,
    activity=True,
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

    if not end_naive:
        raise exc.InvalidAPIRequest("End date required")

    if end_naive < start_naive:
        raise exc.InvalidAPIRequest("End time can't be before the start time")

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
        ticket_url=ticket_url,
    )
    db.session.add(event_date)

    db.session.flush()

    if activity:
        activity = Activity(verb=u"create", object=event_date, target=event_date.event)
        db.session.add(activity)

    if artists is not None:
        event_artists.add_artists_to_date(event_date, artists)

    #    db.session.commit()
    return event_date


def suggest_delete(id, **kwargs):
    # used by unpriviliged users to suggest updates to an event
    token = kwargs.pop("hcaptcha_token", None)
    event_date = get_event_date_or_404(id)
    if not current_user.is_authenticated:
        if not validate_hcaptcha(token):
            raise exc.InvalidAPIRequest("HCaptcha not valid")
    return suggestions.add_suggested_edit(
        event_id=event_date.event_id,
        event_date_id=id,
        creator_id=current_user.get_id(),
        action="delete",
        object_type="EventDate",
        **kwargs
    )


def suggest_update(id, **kwargs):
    # used by unpriviliged users to suggest updates to an event
    token = kwargs.pop("hcaptcha_token", None)
    event_date = get_event_date_or_404(id)
    if not current_user.is_authenticated:
        if not validate_hcaptcha(token):
            raise exc.InvalidAPIRequest("HCaptcha not valid")
    return suggestions.add_suggested_edit(
        event_id=event_date.event_id,
        event_date_id=id,
        creator_id=current_user.get_id(),
        action="update",
        object_type="EventDate",
        **kwargs
    )


def suggest_add(event_id, **kwargs):
    # used by unpriviliged users to suggest updates to an event
    token = kwargs.pop("hcaptcha_token", None)
    events.get_event_or_404(event_id)
    if not current_user.is_authenticated:
        if not validate_hcaptcha(token):
            raise exc.InvalidAPIRequest("HCaptcha not valid")

    return suggestions.add_suggested_edit(
        event_id=event_id,
        action="create",
        object_type="EventDate",
        creator_id=current_user.get_id(),
        **kwargs
    )


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
        start_naive = datetime.strptime(date_time["start"], "%Y-%m-%d %H:%M:%S")
        start_naive = start_naive.replace(tzinfo=None, second=0, microsecond=0)

        if date_time.get("end", None) is None:
            raise exc.InvalidAPIRequest("End date required")
        end_naive = datetime.strptime(date_time["end"], "%Y-%m-%d %H:%M:%S")
        end_naive = end_naive.replace(tzinfo=None, second=0, microsecond=0)

        if end_naive < start_naive:
            raise exc.InvalidAPIRequest("End time can't be before the start time")

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
        # date settings not touched
        # update location of all future eventdates

    if "cancelled" in kwargs:
        event_date.cancelled = kwargs.pop("cancelled")

    if "description" in kwargs:
        event_date.description = kwargs.pop("description", None)

    if "description_attribute" in kwargs:
        event_date.description_attribute = kwargs.pop("description_attribute", None)

    if "url" in kwargs:
        event_date.url = kwargs.pop("url")

    if "ticket_url" in kwargs:
        event_date.ticket_url = kwargs.pop("ticket_url")

    if "size" in kwargs:
        event_date.size = kwargs.pop("size")

    if "remove_artists" in kwargs:
        event_artists.remove_artists_from_date(event_date, kwargs.pop("remove_artists"))

    if "add_artists" in kwargs:
        event_artists.add_artists_to_date(event_date, kwargs.pop("add_artists"))

    if "update_artists" in kwargs:
        event_artists.update_artists(event_date, kwargs.pop("update_artists"))

    # this field is useful for triggering
    # a new version of the parent event object in continuum
    event_date.event.updated_at = datetime.utcnow()

    db.session.flush()
    # had to abandon sqlalchemy-continuum because it requires big integer ID types
    activity = Activity(verb=u"update", object=event_date, target=event_date.event)
    db.session.add(activity)
    # create_notification('UPDATE EVENT', activity, ed.event.followers)
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


def generate_future_event_dates(
    event,
    date_time=None,
    event_location=None,
    rrule=None,
    url=None,
    ticket_url=None,
    next_event_date_description=None,
    next_event_date_description_attribute=None,
    next_event_date_size=None,
    next_event_date_artists=None,
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
        start_naive = datetime.strptime(date_time["start"], "%Y-%m-%d %H:%M:%S")
        start_naive = start_naive.replace(tzinfo=None, second=0, microsecond=0)

        if date_time.get("end", None) is None:
            raise exc.InvalidAPIRequest("End date required")
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
            ticket_url=ticket_url,
            description=next_event_date_description,
            description_attribute=next_event_date_description_attribute,
            size=next_event_date_size,
            artists=next_event_date_artists,
            activity=activity,
        )

    else:

        if url:
            rrule.default_url = url

        else:
            url = rrule.default_url

        # event is recurring
        event.recurring = True
        startdates, enddates = generateRecurringDates(rrule, start_naive, end_naive)

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
                    ticket_url=ticket_url,
                    description=next_event_date_description,
                    description_attribute=next_event_date_description_attribute,
                    size=next_event_date_size,
                    artists=next_event_date_artists,
                    activity=activity,
                )
                # next_event_date_description and artists only used once
                next_event_date_description = None
                next_event_date_artists = None
                next_event_date_description_attribute = None

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

    two_years_away = start.replace(year=start.year + 2)
    ten_years_away = start.replace(year=start.year + 10)

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
            print(startdates)

    else:
        raise exc.InvalidAPIRequest("Invalid recurring_type (1-3)")

    for date in startdates:
        enddates.append(date + duration)

    return startdates, enddates


def delete_event_date(id):
    event_date = get_event_date_or_404(id)
    event = events.get_event_or_404(event_date.event_id)
    # this field is useful for triggering
    # a new version of the parent event object in continuum
    event_date.event.updated_at = datetime.utcnow()
    db.session.delete(event_date)
    db.session.flush()
    activity = Activity(verb=u"delete", object=event_date, target=event_date.event)
    db.session.add(activity)
    db.session.commit()
    return event


def get_event_dates_for_event(event_id):
    event = events.get_event_or_404(event_id)
    return event.event_dates


def query_event_dates(**kwargs):

    # for nearby search
    lat = None
    lng = None
    distance_expression = None
    sort_option = kwargs.get("sort_option", None)
    radius = kwargs.get("radius", None)
    bounds = kwargs.get("bounds", None)

    seconds_start = time.time()

    """
    if kwargs.get("distinct", False) is True:
        # use subquery to return only the next event_date of an event
        date_min = date_time.utcnow()
        if kwargs.get('date_min'):
            date_min = kwargs.get('date_min')

        next_ed = s.query(EventDate).\
                    filter(EventDate.start > date_min).\
                    order_by(EventDate.start.asc()).\
                    subquery()
    """

    next_date = db.session.query(
        EventDate,
        func.row_number()
        .over(partition_by=EventDate.event_id, order_by=EventDate.start.asc())
        .label("rn"),
    ).subquery()

    if kwargs.get("location", None) is not None:
        location = kwargs.get("location")
        lat = float(location["lat"])
        lng = float(location["lng"])

        if lat is None or lng is None:
            raise exc.InvalidAPIRequest("lat and lng are required for nearby search.")

        # potentially faster to keep geometry type
        # than convert degrees to meters.
        # when input is geography type it returns meters
        """
        query = (
            db.session.query(
                EventDate,
                func.ST_Distance(
                    cast(EventLocation.geo, Geography(srid=4326)),
                    cast("SRID=4326;POINT(%f %f)" % (lng, lat), Geography(srid=4326)),
                ).label("distance"),
            )
            .join(Event, EventDate.event_id == Event.id)
            .join(EventLocation, EventDate.location_id == EventLocation.place_id)
        )
        """
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

    joined_tables = [mapper.class_ for mapper in query._join_entities]
    if EventLocation not in joined_tables:
        query = query.join(EventLocation)

    # filter hidden events out
    query = query.filter(Event.hidden == False)  # ignore linter warning here

    if kwargs.get("date_min", None) is not None:
        query = query.filter(EventDate.start >= kwargs.pop("date_min"))
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

    if kwargs.get("favorites", None) is not None:
        if kwargs.get("favorites") is True:
            if not current_user.is_authenticated:
                raise exc.InvalidAPIRequest("Login required for favorites")
            query = query.join(user_event_favorites_table).filter(
                user_event_favorites_table.c.user_id == current_user.id
            )

    if kwargs.get("duration_options", None) is not None:
        duration_options = kwargs.pop("duration_options")
        search_args = [EventDate.duration == option for option in duration_options]
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
        query = query.filter(EventLocation.locality_id == kwargs.pop("locality_id"))
    if kwargs.get("region_id", None) is not None:
        query = query.filter(EventLocation.region_id == kwargs.pop("region_id"))
    if kwargs.get("country_id", None) is not None:
        query = query.filter(EventLocation.country_id == kwargs.pop("country_id"))

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
            Event.__ts_vector__.match(query_text, postgresql_regconfig="english")
        )

    # query = query.order_by(EventDate.start_naive)

    # filter event dates within bounds
    if bounds:

        northEast = bounds["_northEast"]
        southWest = bounds["_southWest"]

        query = query.filter(
            and_(
                or_(
                    and_(
                        southWest["lat"] < northEast["lat"],
                        EventLocation.lat.between(southWest["lat"], northEast["lat"]),
                    ),
                    and_(
                        northEast["lat"] < southWest["lat"],
                        EventLocation.lat.between(northEast["lat"], southWest["lat"]),
                    ),
                ),
                # match lng
                or_(
                    and_(
                        southWest["lng"] < northEast["lng"],
                        EventLocation.lng.between(southWest["lng"], northEast["lng"]),
                    ),
                    and_(
                        northEast["lng"] < southWest["lng"],
                        EventLocation.lng.between(northEast["lng"], southWest["lng"]),
                    ),
                ),
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
                count = query.filter(
                    func.ST_DWithin(
                        cast(EventLocation.geo, Geography(srid=4326)),
                        cast(
                            "SRID=4326;POINT(%f %f)" % (lng, lat), Geography(srid=4326)
                        ),
                        r,
                    )
                ).count()

                # threshold of events required before trying the next radius
                if count >= 10:
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

    if kwargs.get("distinct", None) is True:
        # return only the first event date of an event
        row_number_column = (
            func.row_number()
            .over(partition_by=EventDate.event_id, order_by=asc(EventDate.start))
            .label("row_number")
        )
        query = query.add_column(row_number_column)
        query = query.from_self().filter(row_number_column == 1)

    seconds_end = time.time()
    print("query time in seconds: ", seconds_end - seconds_start)

    results = paginated_results(EventDate, query, **kwargs)
    results.radius = radius
    return results
