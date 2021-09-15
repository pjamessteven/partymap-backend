import pytz
from pytz.exceptions import UnknownTimeZoneError
from timezonefinder import TimezoneFinder
from datetime import datetime
from flask_login import current_user
from geoalchemy2 import func, Geography
from sqlalchemy import cast, or_, and_
from sqlalchemy.orm import with_expression

from pmapi.common.controllers import paginated_results
import pmapi.event_location.controllers as event_locations
import pmapi.event.controllers as events
from pmapi.extensions import db, activity_plugin
from pmapi.event_location.model import EventLocation
from pmapi.event_tag.model import EventTag
from pmapi.event.model import Event
from pmapi import exceptions as exc
from .model import EventDate

# from dateutil.relativedelta import *
from dateutil.rrule import rrule, MO, TU, WE, TH, FR, SA, SU, YEARLY, MONTHLY, WEEKLY

Activity = activity_plugin.activity_cls


def add_event_date_with_datetime(
    event_id,
    dateTime,
    location,
    description=None,
    url=None,
    ticketUrl=None,
    size=None,
    creator=None,
):
    # this function is used by the post eventdate endpoint
    event = events.get_event_or_404(event_id)

    if dateTime:
        date = dateTime.get("date")

        if date.get("start", None) is None:
            raise exc.InvalidAPIRequest("Start date required")
        start = datetime.strptime(date["start"], "%Y-%m-%dT%H:%M:%S.%fZ")
        start_naive = start.replace(tzinfo=None, minute=0, second=0, microsecond=0)

        if date.get("end", None) is None:
            raise exc.InvalidAPIRequest("End date required")
        end = datetime.strptime(date["end"], "%Y-%m-%dT%H:%M:%S.%fZ")
        end_naive = end.replace(tzinfo=None, minute=0, second=0, microsecond=0)

        if dateTime.get("startHours", None) is None:
            raise exc.InvalidAPIRequest("Start hours required")
        start_naive = start_naive.replace(hour=int(dateTime.get("startHours")))

        if dateTime.get("startMinutes", None) is None:
            raise exc.InvalidAPIRequest("Start minutes required")
        start_naive = start_naive.replace(minute=int(dateTime.get("startMinutes")))

        if dateTime.get("endHours", None) is None:
            raise exc.InvalidAPIRequest("Start hours required")
        end_naive = end_naive.replace(hour=int(dateTime.get("endHours")))

        if dateTime.get("endMinutes", None) is None:
            raise exc.InvalidAPIRequest("End minutes required")
        end_naive = end_naive.replace(minute=int(dateTime.get("endMinutes")))

        return add_event_date(
            event=event,
            start_naive=start_naive,
            end_naive=end_naive,
            location=location,
            description=description,
            size=size,
            url=url,
            ticket_url=ticketUrl,
        )

    else:

        raise exc.InvalidAPIRequest(
            "DateTime required for making healthy computer program"
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
    size=None,
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

    start_localized = tz_obj.localize(start_naive)
    start_localized = start_localized.astimezone(pytz.utc)
    start_localized = start_localized.replace(
        tzinfo=None
    )  # strip tz info before adding to db. very important!
    end_localized = tz_obj.localize(end_naive)
    end_localized = end_localized.astimezone(pytz.utc)
    end_localized = end_localized.replace(
        tzinfo=None
    )  # strip tz info before adding to db. very important!

    event_date = EventDate(
        event=event,
        start_naive=start_naive,
        end_naive=end_naive,
        end=end_localized,
        start=start_localized,
        tz=tz,
        location=event_location,
        description=description,
        size=size,
        url=url,
        ticket_url=ticket_url,
    )
    db.session.add(event_date)
    db.session.commit()
    return event_date


def update_event_date(id, **kwargs):
    event_date = get_event_date_or_404(id)

    dateTime = kwargs.get("dateTime", None)
    location = kwargs.get("location", None)

    if dateTime:
        # location required for timezone info
        if location:
            lat = location["geometry"]["location"]["lat"]
            lng = location["geometry"]["location"]["lng"]
        else:
            lat = event_date.location.lat
            lng = event_date.location.lng

        date = dateTime.get("date")

        if date.get("start", None) is None:
            raise exc.InvalidAPIRequest("Start date required")
        start_naive = datetime.strptime(date["start"], "%Y-%m-%dT%H:%M:%S.%fZ")
        start_naive = start_naive.replace(
            tzinfo=None, minute=0, second=0, microsecond=0
        )

        if date.get("end", None) is None:
            raise exc.InvalidAPIRequest("End date required")
        end_naive = datetime.strptime(date["end"], "%Y-%m-%dT%H:%M:%S.%fZ")
        end_naive = end_naive.replace(tzinfo=None, minute=0, second=0, microsecond=0)

        if end_naive < start_naive:
            raise exc.InvalidAPIRequest("End time can't be before the start time")

        if dateTime.get("startHours", None) is None:
            raise exc.InvalidAPIRequest("Start hours required")
        start_naive = start_naive.replace(hour=int(dateTime.get("startHours")))

        if dateTime.get("startMinutes", None) is None:
            raise exc.InvalidAPIRequest("Start minutes required")
        start_naive = start_naive.replace(minute=int(dateTime.get("startMinutes")))

        if dateTime.get("endHours", None) is None:
            raise exc.InvalidAPIRequest("End hours required")
        end_naive = end_naive.replace(hour=int(dateTime.get("endHours")))

        if dateTime.get("endMinutes", None) is None:
            raise exc.InvalidAPIRequest("End minutes required")
        end_naive = end_naive.replace(minute=int(dateTime.get("endMinutes")))

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

        if current_user.is_authenticated:
            event_location_creator = current_user
        else:
            event_location_creator = None

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
        event_date.description = kwargs.pop("description")

    if "url" in kwargs:
        event_date.url = kwargs.pop("url")

    if "ticketUrl" in kwargs:
        event_date.ticket_url = kwargs.pop("ticketUrl")

    if "size" in kwargs:
        event_date.size = kwargs.pop("size")

    event_date.event.updated_at = datetime.utcnow()
    db.session.flush()
    # had to abandon sqlalchemy-continuum because it requires big integer ID types
    # activity = Activity(verb=u"update", object=event_date, target=event_date.event)
    # create_notification('UPDATE EVENT', activity, ed.event.followers)
    # db.session.add(activity)
    db.session.commit()
    return event_date


def generate_future_event_dates(
    event,
    dateTime=None,
    event_location=None,
    rrule=None,
    url=None,
    ticket_url=None,
    next_event_date_description=None,
    next_event_date_size=None,
):

    if url:
        event.default_url = url

    else:
        url = event.default_url

    if ticket_url:
        event.default_ticket_url = ticket_url

    else:
        ticket_url = event.default_ticket_url

    if rrule is None:
        rrule = event.rrule

    if event_location is None:
        event_location = event.default_location

    if dateTime:
        date = dateTime.get("date")

        if date.get("start", None) is None:
            raise exc.InvalidAPIRequest("Start date required")
        start_naive = datetime.strptime(date["start"], "%Y-%m-%dT%H:%M:%S.%fZ")
        start_naive = start_naive.replace(
            tzinfo=None, minute=0, second=0, microsecond=0
        )

        if date.get("end", None) is None:
            raise exc.InvalidAPIRequest("End date required")
        end_naive = datetime.strptime(date["end"], "%Y-%m-%dT%H:%M:%S.%fZ")
        end_naive = end_naive.replace(tzinfo=None, minute=0, second=0, microsecond=0)

        if dateTime.get("startHours", None) is None:
            raise exc.InvalidAPIRequest("Start hours required")
        start_naive = start_naive.replace(hour=int(dateTime.get("startHours")))

        if dateTime.get("startMinutes", None) is None:
            raise exc.InvalidAPIRequest("Start minutes required")
        start_naive = start_naive.replace(minute=int(dateTime.get("startMinutes")))

        # event end time is specified
        if dateTime.get("endHours", None) is None:
            raise exc.InvalidAPIRequest("End hours required")
        end_naive = end_naive.replace(hour=int(dateTime.get("endHours")))

        if dateTime.get("endMinutes", None) is None:
            raise exc.InvalidAPIRequest("End minutes required")
        end_naive = end_naive.replace(minute=int(dateTime.get("endMinutes")))

        # Find timezone info
        try:
            tf = TimezoneFinder()
            tz = tf.timezone_at(lng=event_location.lng, lat=event_location.lat)

        except UnknownTimeZoneError:
            print("TIMEZONE ERROR")

        # delete any event dates in the future
        # because the new recurring profile overrides all old dates
        for ed in event.future_event_dates:
            db.session.delete(ed)

    else:
        # if dateTime not provided,
        # work something out to generate new event dates from
        start_naive = event.last_event_date().start_naive
        end_naive = event.last_event_date().end_naive

        tz = event.last_event_date().tz

    if rrule.separation_count == 0 or rrule is None:
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
            size=next_event_date_size,
        )

    else:
        # event is recurring
        event.recurring = True
        startdates, enddates = generateRecurringDates(rrule, start_naive, end_naive)
        # work out how many dates to generate
        limit = 10 - len(event.future_event_dates)

        if dateTime is None:
            limit += 1

        # generate new event dates
        # limit event dates to 10
        # for start, end in zip(startdates[:10], enddates[:10]):
        for index, start_naive in enumerate(startdates[:limit]):
            if dateTime is None and index == 0:
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
                    size=next_event_date_size,
                )
                # next_event_date_description only used once
                next_event_date_description = None

    db.session.commit()
    return event


# used by events.add_event and events.update_event functions
# to generate a series of dates for an event
# ( should become an automated task in the future )
def generateRecurringDates(rp, start, end=None):

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
    end_weekday = end.weekday()
    end_day = end.day
    end_month = end.month
    end_week_of_month = getWeekInMonth(end)

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
        if end:
            enddates = list(
                rrule(
                    freq=WEEKLY,
                    interval=rp.separation_count,
                    byweekday=end_weekday,
                    dtstart=end,
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

            enddates = list(
                rrule(
                    MONTHLY,
                    interval=rp.separation_count,
                    byweekday=days[end_weekday](end_week_of_month),
                    dtstart=end,
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

            enddates = list(
                rrule(
                    MONTHLY,
                    interval=rp.separation_count,
                    bymonthday=end_day,
                    dtstart=end,
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

            enddates = list(
                rrule(
                    YEARLY,
                    interval=rp.separation_count,
                    bymonth=end_month,
                    byweekday=days[end_weekday](end_week_of_month),
                    dtstart=end,
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
            enddates = list(
                rrule(
                    YEARLY,
                    interval=rp.separation_count,
                    bymonth=end_month,
                    bymonthday=end_day,
                    dtstart=end,
                    until=ten_years_away,
                )
            )

    else:
        raise exc.InvalidAPIRequest("Invalid recurring_type (1-3)")

    return startdates, enddates


def delete_event_date(id):
    event_date = get_event_date_or_404(id)
    db.session.delete(event_date)
    db.session.commit()


def get_event_date_or_404(id):
    event_date = get_event_date(id)
    if not event_date:
        msg = "No such event_date with id {}".format(id)
        raise exc.RecordNotFound(msg)
    return event_date


def get_event_date(id):
    return EventDate.query.get(id)


def get_event_dates_for_event(event_id):
    event = events.get_event_or_404(event_id)
    return event.event_dates


def query_event_dates(**kwargs):

    # for nearby search
    lat = None
    lng = None
    distance_expression = None

    if "location" in kwargs and kwargs.get("location"):
        location = kwargs.get("location")
        lat = location["lat"]
        lng = location["lng"]

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
                )
            )
            .join(Event, EventDate.event_id == Event.id)
            .join(EventLocation, EventDate.location_id == EventLocation.place_id)
        )

    else:
        query = db.session.query(EventDate)
        query = query.join(Event)

    # filter cancelled events out
    query = query.filter(EventDate.cancelled != True)

    # filter hidden events out
    query = query.filter(Event.hidden == False)  # ignore linter warning here

    if "date_min" in kwargs:
        query = query.filter(EventDate.start_naive >= kwargs.pop("date_min"))
    if "date_max" in kwargs:
        date_max = kwargs.pop("date_max")
        query = query.filter(
            and_(
                or_(
                    EventDate.end_naive <= date_max,
                    EventDate.end_naive.is_(None),
                ),
                EventDate.start_naive <= date_max,
            )
        )

    if "tags" in kwargs:
        tags = kwargs.pop("tags")
        for tag in tags:
            query = query.filter(Event.event_tags.any(EventTag.tag_id == tag))

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

    # if bounds and not location
    if ("bounds" in kwargs) and ("location" not in kwargs):
        # bounds search is to return event dates that are in current view
        # on the map
        query = query.join(EventLocation)
        bounds = kwargs.pop("bounds")
        northEast = bounds["_northEast"]
        southWest = bounds["_southWest"]

        # convert negative longitude coordinates
        if southWest["lng"] < -180:
            southWest["lng"] += 360
            northEast["lng"] += 360

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
        query = query.order_by(EventDate.start_naive)

    if lat and lng:
        # nearby search
        radii = [1000, 5000, 10000, 20000, 50000, 100000, 200000, 500000]
        for radius in radii:
            count = query.filter(
                func.ST_DWithin(
                    cast(EventLocation.geo, Geography(srid=4326)),
                    cast("SRID=4326;POINT(%f %f)" % (lng, lat), Geography(srid=4326)),
                    radius,
                )
            ).count()

            # threshold of events required before trying the next radius
            if count >= 5:
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
                break

        query = query.order_by(distance_expression.asc(), EventDate.start_naive.asc())

    return paginated_results(EventDate, query, **kwargs)
