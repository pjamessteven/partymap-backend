import pytz
from pytz.exceptions import UnknownTimeZoneError
from timezonefinder import TimezoneFinder
from datetime import datetime
from flask import jsonify
from geoalchemy2 import func, Geography
from sqlalchemy import cast, or_, and_
from pytz import timezone, utc
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


def add_event_date_with_datetime(event_id, dateTime, location, description, url):
    # this function is used by the post eventdate endpoint
    event = events.get_event_or_404(event_id)

    if dateTime:
        date = dateTime.get("date")

        event_start = datetime.strptime(date["start"], "%Y-%m-%dT%H:%M:%S.%fZ")
        event_start = event_start.replace(tzinfo=None)
        event_end = None
        all_day = True

        if date.get("end", None):
            print("has end")
            event_end = datetime.strptime(date["end"], "%Y-%m-%dT%H:%M:%S.%fZ")
            event_end = event_end.replace(tzinfo=None)

        # event start time is specified
        if dateTime.get("startHours", None):
            print("start date triggered")
            all_day = False
            event_start = event_start.replace(hour=int(dateTime.get("startHours")))
            if dateTime.get("startMinutes") is not None:
                event_start = event_start.replace(
                    minute=int(dateTime.get("startMinutes"))
                )

        # event end time is specified
        if dateTime.get("endHours", None) and date.get("end", None):
            print("end date triggered")
            all_day = False
            event_end = event_end.replace(hour=int(dateTime.get("endHours")))
            if dateTime.get("endMinutes") is not None:
                event_end = event_end.replace(minute=int(dateTime.get("endMinutes")))

        return add_event_date(
            event,
            event_start,
            end=event_end,
            all_day=all_day,
            location=location,
            description=description,
            url=url,
        )

    else:
        raise exc.InvalidAPIRequest()


def add_event_date(
    event,
    start,
    end=None,
    all_day=False,
    event_location=None,
    location=None,
    tz=None,
    url=None,
    description=None,
    **kwargs
):
    """accepts naive start and end dates and derives timezone from location
    if it not provided"""

    location = kwargs.pop("location")

    if "tz" in kwargs:
        tz_obj = pytz.timezone(kwargs.pop("tz"))
    else:
        tf = TimezoneFinder()
        tz = tf.timezone_at(lng=location.lng, lat=location.lat)
        tz_obj = pytz.timezone(tz)

    event_location = event_locations.get_event_location(location.place_id)
    if not event_location:
        event_location = event_locations.add_new_event_location(**location)

    start_localized = tz_obj.localize(kwargs.pop("start"))
    start_localized = start_localized.astimezone(timezone.utc)
    # strip tz info before adding to db. very important!
    start_localized = start_localized.replace(tzinfo=None)
    # check if there is an enddate
    end_localized = None

    if end:
        end_localized = end
        end_localized = end_localized.astimezone(timezone.utc)
        end_localized = end_localized.replace(tzinfo=None)
    ed = EventDate(
        event=event,
        event_start_naive=start,
        event_end_naive=end,
        event_end=end_localized,
        event_start=start_localized,
        all_day=all_day,
        tz=tz,
        location=event_location,
        url=url,
    )
    db.session.add(ed)


def update_event_date(id, **kwargs):
    event_date = get_event_date_or_404(id)

    dateTime = kwargs.get("dateTime", None)
    location = kwargs.get("location", None)

    if "cancelled" in kwargs:
        event_date.cancelled = kwargs.pop("cancelled")

    if "description" in kwargs:
        event_date.description = kwargs.pop("description")

    if "url" in kwargs:
        event_date.url = kwargs.pop("url")

    if "dateTime":
        # location required for timezone info
        if "location":
            lat = location["geometry"]["location"]["lat"]
            lng = location["geometry"]["location"]["lng"]
        else:
            lat = event_date.location.lat
            lng = event_date.location.lng
        geocode = reverse_geocode.search([(lat, lng)])[0]

        date = dateTime.get("date")
        event_start = datetime.strptime(date["start"], "%Y-%m-%dT%H:%M:%S.%fZ")

        event_end = None
        all_day = True

        if dateTime.get("end", None):
            print("has end")
            event_end = datetime.strptime(date["end"], "%Y-%m-%dT%H:%M:%S.%fZ")

        # event start time is specified
        if dateTime.get("startHours", None):
            print("start date triggered")
            all_day = False
            event_start = event_start.replace(hour=int(dateTime.get("startHours")))
            if dateTime.get("startMinutes") is not None:
                event_start = event_start.replace(
                    minute=int(dateTime.get("startMinutes"))
                )

        # event end time is specified
        if dateTime.get("endHours", None) is not None and event_end is not None:
            print("end date triggered")
            all_day = False
            event_end = event_end.replace(hour=int(dateTime.get("endHours")))
            if dateTime.get("endMinutes") is not None:
                event_end = event_end.replace(minute=int(dateTime.get("endMinutes")))
        #
        try:
            # ADD CORRECT TIMEZONE TO DATE TIME AND THEN CONVERT TO UTC
            tf = TimezoneFinder()
            tz = tf.timezone_at(lng=lng, lat=lat)
            tz_obj = timezone(tz)

        except UnknownTimeZoneError:
            print("TIMEZONE ERROR")
            pass  # {handle error}

        """
        Date should be received as a naive date
        ie. the local time where the event is happening with no tz info.
        """
        event_start = event_start.replace(tzinfo=None)
        event_start_naive = event_start
        event_start = tz_obj.localize(event_start)
        event_start = event_start.astimezone(utc)
        event_start = event_start.replace(tzinfo=None)
        event_end_naive = None
        if event_end is not None:
            event_end = event_end.replace(tzinfo=None)
            event_end_naive = event_end
            event_end = tz_obj.localize(event_end)
            event_end = event_end.astimezone(utc)
            event_end = event_end.replace(tzinfo=None)

        event_date.event_start = event_start
        event_date.event_end = event_end
        event_date.event_start_naive = event_start_naive
        event_date.event_end_naive = event_end_naive
        event_date.all_day = all_day
        event_date.tz = tz
        print("start naive")
        print(event_start_naive)
        print("end naive")
        print(event_end_naive)
        print("start")
        print(event_start)
        print("end")
        print(event_end)

    if location:
        lat = location["geometry"]["location"]["lat"]
        lng = location["geometry"]["location"]["lng"]
        location_name = location["name"]
        location_description = location["description"]
        location_types = location["types"]
        location_place_id = location["place_id"]

        geocode = reverse_geocode.search([(lat, lng)])[0]
        try:
            # ADD CORRECT TIMEZONE TO DATE TIME AND THEN CONVERT TO UTC
            tf = TimezoneFinder()
            tz = tf.timezone_at(lng=lng, lat=lat)
            tz_obj = timezone(tz)

        except UnknownTimeZoneError:
            print("TIMEZONE ERROR")
            pass  # {handle error}

        location_type_objects = []
        for t in location_types:
            elt = EventLocationType(type=t)
            db.session.merge(elt)
            location_type_objects.append(elt)

        location = EventLocation(
            geohash=pgh.encode(lat, lng),
            # For geodetic coordinates, X is longitude and Y is latitude
            geo="SRID=4326;POINT ({0} {1})".format(lng, lat),
            name=location_name,
            description=location_description,
            types=location_type_objects,
            lat=lat,
            lng=lng,
            country_code=geocode["country_code"],
            city=geocode["city"],
            place_id=location_place_id,
        )
        location = db.session.merge(location)
        event_date.location = location
        event_date.tz = tz
        # date settings not touched
        # update location of all future eventdates
    db.session.flush()
    activity = Activity(verb=u"update", object=event_date, target=event_date.event)
    # create_notification('UPDATE EVENT', activity, ed.event.followers)
    db.session.add(activity)
    db.session.commit()

    return event_date


def generate_future_event_dates(
    event, dateTime=None, location=None, rrule=None, url=None
):

    if event:
        print("if event")
        if url:
            event.default_url = url
            print("if url")

        else:
            url = event.default_url
            print("else url")

        if rrule:
            print(rrule)
            recurring_type = rrule.get("recurringType")
            print(recurring_type)
            separation_count = rrule.get("separationCount")
            day_of_week = (
                int(rrule.get("dayOfWeek"))
                if rrule.get("dayOfWeek") is not None
                else None
            )
            day_of_month = (
                int(rrule.get("dayOfMonth"))
                if rrule.get("dayOfMonth") is not None
                else None
            )
            week_of_month = (
                int(rrule.get("weekOfMonth"))
                if rrule.get("weekOfMonth") is not None
                else None
            )
            month_of_year = (
                int(rrule.get("monthOfYear"))
                if rrule.get("monthOfYear") is not None
                else None
            )

            # update event rrule
            if event.rrule:
                db.session.delete(event.rrule)
                db.session.commit()

            rrule = Rrule(
                event=event,
                recurring_type=recurring_type,
                separation_count=separation_count,
                day_of_week=day_of_week,
                day_of_month=day_of_month,
                week_of_month=week_of_month,
                month_of_year=month_of_year,
            )
            db.session.add(rrule)
            db.session.flush()
        else:
            rrule = event.rrule

        if location:
            event_location = event_locations.get_event_location(location["place_id"])
            if event_location is None:
                event_location = event_locations.add_new_event_location(**location)

        else:
            event_location = event.last_event().location

        if dateTime:
            date = dateTime.get("date")

            event_start = datetime.strptime(date["start"], "%Y-%m-%dT%H:%M:%S.%fZ")
            event_start = event_start.replace(tzinfo=None)
            event_end = None
            all_day = True

            if date.get("end", None):
                print("has end")
                event_end = datetime.strptime(date["end"], "%Y-%m-%dT%H:%M:%S.%fZ")
                event_end = event_end.replace(tzinfo=None)

            # event start time is specified
            if dateTime.get("startHours", None):
                print("start date triggered")
                all_day = False
                event_start = event_start.replace(hour=int(dateTime.get("startHours")))
                if dateTime.get("startMinutes") is not None:
                    event_start = event_start.replace(
                        minute=int(dateTime.get("startMinutes"))
                    )

            # event end time is specified
            if dateTime.get("endHours", None) and date.get("end", None):
                print("end date triggered")
                all_day = False
                event_end = event_end.replace(hour=int(dateTime.get("endHours")))
                if dateTime.get("endMinutes") is not None:
                    event_end = event_end.replace(
                        minute=int(dateTime.get("endMinutes"))
                    )

            # Find timezone info
            try:
                tf = TimezoneFinder()
                tz = tf.timezone_at(lng=event_location.lng, lat=event_location.lat)

            except UnknownTimeZoneError:
                print("TIMEZONE ERROR")

            # delete any event dates in the future
            now = datetime.utcnow()
            for ed in event.event_dates:
                if ed.event_start > now:
                    db.session.delete(ed)

        else:
            # if dateTime not provided,
            # work something out to generate new event dates from
            event_start = event.last_event().event_start_naive
            event_end = event.last_event().event_end_naive

            tz = event.last_event().tz

        if separation_count != 0:
            event.recurring = True
            print(event_end)
            startdates, enddates = generateRecurringDates(rrule, event_start, event_end)

            # work out how many dates to generate
            if dateTime:
                limit = 10 - len(event.future_event_dates())
                if event.last_event():
                    print("last event", event.last_event())
                    db.session.delete(event.last_event())
            else:
                limit = 10

            # limit event dates to 10
            # for start, end in zip(startdates[:10], enddates[:10]):
            for index, startdate_naive in enumerate(startdates[:limit]):
                enddate_naive = None
                try:
                    if enddates[index] is not None:
                        enddate_naive = enddates[index]
                except IndexError:
                    print("no enddate")
                add_event_date(
                    event=event,
                    start=startdate_naive,
                    end=enddate_naive,
                    location=event_location,
                    all_day=all_day,
                    tz=tz,
                    url=url,
                )
        else:
            # event is a one-off
            event.recurring = False
            add_event_date(
                event=event,
                start=event_start,
                end=event_end,
                location=event_location,
                all_day=all_day,
                tz=tz,
                url=url,
            )

        db.session.commit()
        return jsonify(event.to_dict()), 201

    else:
        print("failed - no event")
        return


def generateRecurringDates(rp, event_start, event_end):

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

    print(rp.to_dict())

    two_years_away = event_start.replace(year=event_start.year + 2)
    ten_years_away = event_start.replace(year=event_start.year + 10)

    start_weekday = event_start.weekday()
    end_weekday = event_end.weekday()

    start_day = event_start.day
    end_day = event_end.day

    start_month = event_start.month
    end_month = event_end.month

    start_week_of_month = getWeekInMonth(event_start)
    end_week_of_month = getWeekInMonth(event_end)

    if rp.recurring_type == 2:
        if rp.week_of_month:
            print("recurring monthly event")
            print(days[rp.day_of_week])
            print(event_start)
            startdates = list(
                rrule(
                    MONTHLY,
                    interval=rp.separation_count,
                    byweekday=days[start_weekday](start_week_of_month),
                    dtstart=event_start,
                    until=ten_years_away,
                )
            )

            if event_end:
                enddates = list(
                    rrule(
                        MONTHLY,
                        interval=rp.separation_count,
                        byweekday=days[end_weekday](end_week_of_month),
                        dtstart=event_end,
                        until=ten_years_away,
                    )
                )
        else:
            print("absolute monthly event")
            startdates = list(
                rrule(
                    MONTHLY,
                    interval=rp.separation_count,
                    bymonthday=start_day,
                    dtstart=event_start,
                    until=ten_years_away,
                )
            )

            if event_end:
                enddates = list(
                    rrule(
                        MONTHLY,
                        interval=rp.separation_count,
                        bymonthday=end_day,
                        dtstart=event_end,
                        until=ten_years_away,
                    )
                )

    elif rp.recurring_type == 3:
        if rp.week_of_month:
            print("recurring yearly event")
            startdates = list(
                rrule(
                    YEARLY,
                    interval=rp.separation_count,
                    bymonth=start_month,
                    byweekday=days[start_weekday](start_week_of_month),
                    dtstart=event_start,
                    until=ten_years_away,
                )
            )

            if event_end:
                enddates = list(
                    rrule(
                        YEARLY,
                        interval=rp.separation_count,
                        bymonth=end_month,
                        byweekday=days[end_weekday](end_week_of_month),
                        dtstart=event_end,
                        until=ten_years_away,
                    )
                )
        else:
            print("absolute yearly event")
            startdates = list(
                rrule(
                    YEARLY,
                    interval=rp.separation_count,
                    bymonth=start_month,
                    bymonthday=start_day,
                    dtstart=event_start,
                    until=ten_years_away,
                )
            )
            if event_end:
                enddates = list(
                    rrule(
                        YEARLY,
                        interval=rp.separation_count,
                        bymonth=end_month,
                        bymonthday=end_day,
                        dtstart=event_end,
                        until=ten_years_away,
                    )
                )

    elif rp.recurring_type == 1:
        print("recurring weekly event")
        startdates = list(
            rrule(
                freq=WEEKLY,
                interval=rp.separation_count,
                byweekday=start_weekday,
                dtstart=event_start,
                until=two_years_away,
            )
        )
        if event_end:
            enddates = list(
                rrule(
                    freq=WEEKLY,
                    interval=rp.separation_count,
                    byweekday=end_weekday,
                    dtstart=event_end,
                    until=two_years_away,
                )
            )

    print("recurring dates:")
    print(startdates)
    print(enddates)

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

    if "location" in kwargs and kwargs.get("location"):
        location = kwargs.pop("location")
        print(location, "test loc")
        lat = location["lat"]
        lng = location["lng"]
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

    if "bounds" in kwargs and "location" not in kwargs:
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
