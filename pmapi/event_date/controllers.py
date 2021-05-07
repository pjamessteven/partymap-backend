import pytz
from pytz.exceptions import UnknownTimeZoneError
from timezonefinder import TimezoneFinder
from datetime import datetime
from flask import jsonify
from flask_login import current_user
from geoalchemy2 import func, Geography
from sqlalchemy import cast, or_, and_
import reverse_geocode
import pygeohash as pgh

from pmapi.common.controllers import paginated_results
import pmapi.event_location.controllers as event_locations
import pmapi.event.controllers as events
from pmapi.extensions import db, activity_plugin
from pmapi.event.model import Rrule
from pmapi.event_location.model import EventLocation, EventLocationType
from pmapi.event_tag.model import EventTag
from pmapi.event.model import Event
from pmapi import exceptions as exc
from .model import EventDate

# from dateutil.relativedelta import *
from dateutil.rrule import rrule, MO, TU, WE, TH, FR, SA, SU, YEARLY, MONTHLY, WEEKLY

Activity = activity_plugin.activity_cls


def add_event_date_with_datetime(
    event_id, dateTime, location, description=None, url=None, creator=None
):
    # this function is used by the post eventdate endpoint
    event = events.get_event_or_404(event_id)

    if dateTime:
        date = dateTime.get("date")

        start = datetime.strptime(date["start"], "%Y-%m-%dT%H:%M:%S.%fZ")
        start_naive = start.replace(tzinfo=None)
        print("start naive", start_naive)
        end = None

        if date.get("end", None):
            end = datetime.strptime(date["end"], "%Y-%m-%dT%H:%M:%S.%fZ")
            end_naive = end.replace(tzinfo=None)
            print("end naive", end_naive)

        # event start time is specified
        if dateTime.get("startHours", None):
            start_naive = start_naive.replace(hour=int(dateTime.get("startHours")))
            if dateTime.get("startMinutes") is not None:
                start_naive = start_naive.replace(
                    minute=int(dateTime.get("startMinutes"))
                )
            print("start hours", start)

        # event end time is specified
        if dateTime.get("endHours", None) and date.get("end", None):
            end_naive = end_naive.replace(hour=int(dateTime.get("endHours")))
            if dateTime.get("endMinutes") is not None:
                end_naive = end_naive.replace(minute=int(dateTime.get("endMinutes")))
            print("end_hours", end)

        return add_event_date(
            event=event,
            start_naive=start_naive,
            end_naive=end_naive,
            location=location,
            description=description,
            url=url,
            creator=creator,
        )

    else:
        raise exc.InvalidAPIRequest()


def add_event_date(
    start_naive,
    event,
    location=None,  # this parameter is used by direct api calls to this function
    event_location=None,  # this parameter is only used by generate_event_dates
    creator=None,
    end_naive=None,
    tz=None,
    url=None,
    description=None,
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

    start_localized = tz_obj.localize(start_naive)
    start_localized = start_localized.astimezone(pytz.utc)
    # strip tz info before adding to db. very important!
    start_localized = start_localized.replace(tzinfo=None)
    # check if there is an enddate
    end_localized = None

    if end_naive:
        end_localized = tz_obj.localize(end_naive)
        end_localized = end_localized.astimezone(pytz.utc)
        end_localized = end_localized.replace(tzinfo=None)

        if end_naive < start_naive:
            raise exc.InvalidAPIRequest("End date must be before start date")

    print(start_localized)
    event_date = EventDate(
        event=event,
        start_naive=start_naive,
        end_naive=end_naive,
        end=end_localized,
        start=start_localized,
        tz=tz,
        location=event_location,
        description=description,
        url=url,
        creator=creator,
    )
    db.session.add(event_date)
    db.session.commit()
    return event_date


def update_event_date(id, **kwargs):
    event_date = get_event_date_or_404(id)

    dateTime = kwargs.get("dateTime", None)
    location = kwargs.get("location", None)

    if "dateTime":
        # location required for timezone info
        if "location":
            lat = location["geometry"]["location"]["lat"]
            lng = location["geometry"]["location"]["lng"]
        else:
            lat = event_date.location.lat
            lng = event_date.location.lng

        date = dateTime.get("date")
        start = datetime.strptime(date["start"], "%Y-%m-%dT%H:%M:%S.%fZ")
        end = None

        if date.get("end", None):
            print("has end")
            end = datetime.strptime(date["end"], "%Y-%m-%dT%H:%M:%S.%fZ")

        # event start time is specified
        if dateTime.get("startHours", None):
            start = start.replace(hour=int(dateTime.get("startHours")))
            if dateTime.get("startMinutes") is not None:
                start = start.replace(minute=int(dateTime.get("startMinutes")))

        # event end time is specified
        if dateTime.get("endHours", None) is not None and end is not None:
            end = end.replace(hour=int(dateTime.get("endHours")))
            if dateTime.get("endMinutes") is not None:
                end = end.replace(minute=int(dateTime.get("endMinutes")))
        #
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
        start = start.replace(tzinfo=None)
        start_naive = start
        start = tz_obj.localize(start)
        start = start.astimezone(pytz.utc)
        start = start.replace(tzinfo=None)
        end_naive = None
        if end is not None:
            end = end.replace(tzinfo=None)
            end_naive = end
            end = tz_obj.localize(end)
            end = end.astimezone(pytz.utc)
            end = end.replace(tzinfo=None)

            if end < start:
                raise exc.InvalidAPIRequest("End date must be before start date")

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

    db.session.flush()
    # had to abandon sqlalchemy-continuum because it requires big integer ID types
    # activity = Activity(verb=u"update", object=event_date, target=event_date.event)
    # create_notification('UPDATE EVENT', activity, ed.event.followers)
    # db.session.add(activity)
    db.session.commit()

    return event_date


def generate_future_event_dates(
    event, dateTime=None, location=None, rrule=None, url=None
):

    if url:
        event.default_url = url

    else:
        url = event.default_url

    if rrule is None:
        rrule = event.rrule

    if location:
        event_location = event_locations.get_location(location["place_id"])
        if event_location is None:
            event_location = event_locations.add_new_event_location(**location)

    else:
        event_location = event.default_location

    if dateTime:
        date = dateTime.get("date")

        start_naive = datetime.strptime(date["start"], "%Y-%m-%dT%H:%M:%S.%fZ")
        start_naive = start_naive.replace(tzinfo=None)
        end_naive = None

        if date.get("end", None):
            end_naive = datetime.strptime(date["end"], "%Y-%m-%dT%H:%M:%S.%fZ")
            end_naive = end_naive.replace(tzinfo=None)

        # event start time is specified
        if dateTime.get("startHours", None):
            start_naive = start_naive.replace(hour=int(dateTime.get("startHours")))
            if dateTime.get("startMinutes") is not None:
                start_naive = start_naive.replace(
                    minute=int(dateTime.get("startMinutes"))
                )

        # event end time is specified
        if dateTime.get("endHours", None) and date.get("end", None):
            end_naive = end_naive.replace(hour=int(dateTime.get("endHours")))
            if dateTime.get("endMinutes") is not None:
                end_naive = end_naive.replace(minute=int(dateTime.get("endMinutes")))

        # Find timezone info
        try:
            tf = TimezoneFinder()
            tz = tf.timezone_at(lng=event_location.lng, lat=event_location.lat)

        except UnknownTimeZoneError:
            print("TIMEZONE ERROR")

        # delete any event dates in the future
        # because the new recurring profile overrides all old dates
        now = datetime.utcnow()
        for ed in event.event_dates:
            if ed.start > now:
                db.session.delete(ed)

    else:
        # if dateTime not provided,
        # work something out to generate new event dates from
        start_naive = event.last_event().start_naive
        end_naive = event.last_event().end_naive

        tz = event.last_event().tz

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
        )

    else:
        # event is recurring
        event.recurring = True
        startdates, enddates = generateRecurringDates(rrule, start_naive, end_naive)

        # work out how many dates to generate
        limit = 10 - len(event.future_event_dates())
        # if event.last_event():
        # db.session.delete(event.last_event())

        print("limit", limit)
        print("startdates", startdates)

        # generate new event dates
        # limit event dates to 10
        # for start, end in zip(startdates[:10], enddates[:10]):
        for index, start_naive in enumerate(startdates[:limit]):
            end_naive = None
            try:
                if enddates[index] is not None:
                    end_naive = enddates[index]
            except IndexError:
                print("no enddate")

            add_event_date(
                event=event,
                start_naive=start_naive,
                end_naive=end_naive,
                event_location=event_location,
                tz=tz,
                url=url,
            )

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
        result = 1
        for x in range(len(weeks)):
            if date.day in weeks[x]:
                result += 1
        return result

    startdates = []
    enddates = []

    two_years_away = start.replace(year=start.year + 2)
    ten_years_away = start.replace(year=start.year + 10)

    start_weekday = start.weekday()
    start_day = start.day
    start_month = start.month
    start_week_of_month = getWeekInMonth(start)

    end_weekday = None
    end_day = None
    end_month = None
    end_week_of_month = None
    if end:
        end_weekday = end.weekday()
        end_day = end.day
        end_month = end.month
        end_week_of_month = getWeekInMonth(end)

    if rp.recurring_type == 2:
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

            if end:
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
            startdates = list(
                rrule(
                    MONTHLY,
                    interval=rp.separation_count,
                    bymonthday=start_day,
                    dtstart=start,
                    until=ten_years_away,
                )
            )

            if end:
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

            if end:
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
            if end:
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

    elif rp.recurring_type == 1:
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
    print("called")
    # for nearby search
    lat = None
    lng = None
    print(kwargs)

    if "location" in kwargs and kwargs.get("location"):
        location = kwargs.pop("location")
        print(location, "test loc")
        lat = location["lat"]
        lng = location["lon"]
        if lat is None or lng is None:
            raise exc.InvalidAPIRequest("lat and lng are required for nearby search.")

        # potentially faster to keep geometry type
        # than convert degrees to meters.
        # when input is geography type it returns meters
        query = (
            db.session.query(
                EventDate,
                func.ST_Distance(
                    cast(EventLocation.geo, Geography(srid=4326)),
                    cast("SRID=4326;POINT(%f %f)" % (lng, lat), Geography(srid=4326)),
                ).label("distance"),
            )
            .join(EventLocation)
            .join(EventDate.event)
        )

    else:
        query = db.session.query(EventDate)

    # filter cancelled events out
    query = query.filter(EventDate.cancelled is not True)

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
        query = query.join(Event)
        for tag in tags:
            query = query.filter(Event.event_tags.any(EventTag.tag_id == tag))

    if "bounds" in kwargs and "location" not in kwargs:
        print("bounds")
        # bounds search is to return event dates that are in current view
        # on the map
        query = query.join(EventLocation)
        bounds = kwargs.pop("bounds")
        northEast = bounds["_northEast"]
        southWest = bounds["_southWest"]
        query = query.filter(
            and_(
                EventLocation.lat < northEast["lat"],
                EventLocation.lat > southWest["lat"],
                EventLocation.lng < northEast["lng"],
                EventLocation.lng > southWest["lng"],
            )
        )
    if lat and lng:
        # nearby search
        radii = [1000, 5000, 10000, 20000, 50000, 100000, 200000, 500000]
        for radius in radii:
            print(radius)
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
            """
                if location is not None:
                    # if location query has been run,
                    # append distance to minified object
                    event_dates_with_location = []
                    for ed in event_dates:
                        result = ed[0].minified()
                        result["distance"] = int(ed[1] / 1000)
                        event_dates_with_location.append(result)
                    return event_dates_with_location

            if event_dates is None:
                return jsonify({"message": "No events in 500km radius"}), 204
        """

    return paginated_results(EventDate, query=query, **kwargs)
