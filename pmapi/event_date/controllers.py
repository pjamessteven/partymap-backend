import pmapi.event_location.controllers as event_locations
from pmapi.event_date.model import EventDate
from pmapi.extensions import db
from pmapi.event.model import Rrule
import pytz
from pytz.exceptions import UnknownTimeZoneError
from timezonefinder import TimezoneFinder
from datetime import datetime, timezone
from flask import jsonify
from geoalchemy2.elements import WKTElement
import json
from geoalchemy2 import Geometry, func, Geography
from sqlalchemy import cast, or_, and_

from pmapi.event_location.model import EventLocation

# from dateutil.relativedelta import *
from dateutil.rrule import rrule, MO, TU, WE, TH, FR, SA, SU, YEARLY, MONTHLY, WEEKLY


def add_event_date(
    event,
    start,
    end,
    all_day,
    event_location=None,
    location=None,
    tz=None,
    url=None,
    description=None,
):
    """accepts naive start and end dates and derives timezone from location
    if it not provided"""
    if tz:
        tz_obj = pytz.timezone(tz)
    else:
        tf = TimezoneFinder()
        tz = tf.timezone_at(lng=location.lng, lat=location.lat)
        tz_obj = pytz.timezone(tz)

    if location:
        event_location = event_locations.get_event_location(location.place_id)
        if not event_location:
            event_location = event_locations.add_new_event_location(**location)

    if not event_location:
        # throw error
        pass

    start_localized = tz_obj.localize(start)
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


def update_event_date():
    pass


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
                if dateTime.get("startHours") is not None:
                    event_start = event_start.replace(
                        hour=int(dateTime.get("startHours"))
                    )
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


def query_event_dates(min, max=None, location=None, bounds=None, tags=None, page=None):

    if min:
        min = datetime.utcfromtimestamp(int(min) / 1000)
    else:
        min = datetime.utcnow()

    if max is None or max == "Infinity":
        max = datetime.utcnow().replace(
            year=datetime.utcnow().year + 2
        )  # two years from now
    else:
        max = datetime.utcfromtimestamp(int(max) / 1000)

    if location is not None:
        location = json.loads(location)
        radii = [1000, 5000, 10000, 20000, 50000, 100000, 200000, 500000]
        event_dates = None
        lat = float(location["lat"])
        lon = float(location["lon"])
        # wkt_element = WKTElement("POINT(%f %f)" % (lon, lat), 4326)
        # return event dates by location and add a distance column
        for radius in radii:
            print(radius)
            count = (
                db.session.query(
                    EventDate,
                    func.ST_Distance(
                        cast(EventLocation.geo, Geography(srid=4326)),
                        cast(
                            "SRID=4326;POINT(%f %f)" % (lon, lat), Geography(srid=4326)
                        ),
                    ).label("distance")
                    # potentially faster to keep geometry type then convert degrees to meters.
                    # when input is geography type it returns meters
                )
                .join(EventLocation)
                .join(EventDate.event)
                .filter(
                    func.ST_DWithin(
                        cast(EventLocation.geo, Geography(srid=4326)),
                        cast(
                            "SRID=4326;POINT(%f %f)" % (lon, lat), Geography(srid=4326)
                        ),
                        radius,
                    )
                )
                .count()
            )
            if count >= 5:
                event_dates = (
                    db.session.query(
                        EventDate,
                        func.ST_Distance(
                            cast(EventLocation.geo, Geography(srid=4326)),
                            cast(
                                "SRID=4326;POINT(%f %f)" % (lon, lat),
                                Geography(srid=4326),
                            ),
                        ).label("distance")
                        # potentially faster to keep geometry type then convert degrees to meters.
                        # when input is geography type it returns meters
                    )
                    .join(EventLocation)
                    .join(EventDate.event)
                    .filter(
                        func.ST_DWithin(
                            cast(EventLocation.geo, Geography(srid=4326)),
                            cast(
                                "SRID=4326;POINT(%f %f)" % (lon, lat),
                                Geography(srid=4326),
                            ),
                            radius,
                        )
                    )
                )
                break
                # using geography instead of geometry for 4326 dwithin function is much faster
                # could possibly increase performace with boolean use_spheroid = False at the cost of accuracy

        if event_dates is None:
            return jsonify({"message": "No events in 500km radius"}), 204

    else:
        event_dates = (
            db.session.query(EventDate).join(EventDate.location).join(EventDate.event)
        )
        # this used to be EventLocation.event - I don't know why? maybe I broke it

    # filter dates
    event_dates = event_dates.filter(
        or_(
            and_(
                EventDate.event_start_naive >= min,
                and_(
                    EventDate.event_end_naive <= max, EventDate.event_end_naive >= min
                ),
            ),
            and_(
                EventDate.event_start_naive >= min, EventDate.event_start_naive <= max
            ),
        )
    )

    # filter cancelled events out
    event_dates = event_dates.filter(EventDate.cancelled is False)

    """ the old version of this query will filter any events happening in the range.
            this is kind of confusing for users. might be good for a 'happening now' type query
            for homepage.
            this version was more suitable when navigation was done with a slider, but I think
            it would also mean that the date list would get clogged up with 'in progress' events
            (which could feel spammy)
            event_dates = event_dates.filter(
                            or_(
                                and_(EventDate.event_end>min,EventDate.event_end<max),
                                and_(EventDate.event_start>min,and_(EventDate.event_end<max, EventDate.event_end>min)),
                                and_(EventDate.event_start>min,EventDate.event_start<max),
                                and_(EventDate.event_start<min, EventDate.event_end>max)
                                )
                            )
        """
    print(event_dates.all())

    # filter location
    # filter bounds if no location specified
    if bounds is not None and location is None:
        print("bounds: ", bounds)
        bounds = json.loads(bounds)
        northEast = bounds["_northEast"]
        southWest = bounds["_southWest"]
        event_dates = event_dates.filter(
            and_(
                EventLocation.lat < northEast["lat"],
                EventLocation.lat > southWest["lat"],
                EventLocation.lng < northEast["lng"],
                EventLocation.lng > southWest["lng"],
            )
        )

    # filter tags
    if request.args.get("tags[]"):
        tags = request.args.getlist("tags[]")
        print(tags)
        for tag in tags:
            event_dates = event_dates.filter(
                or_(
                    EventDate.artists.any(EventArtist.artist_name == tag),
                    Event.event_tags.any(EventTag.tag_id == tag),
                ),
            )

    # order by date
    event_dates = event_dates.order_by(EventDate.event_start.asc())

    if page is not None and page > 0:
        # paginate
        event_dates_paginated = event_dates.paginate(page, per_page)
        event_dates = event_dates_paginated.items

    print(event_dates)

    if location is not None:
        # if location query has been run,
        # append distance to minified object
        event_dates_with_location = []
        for ed in event_dates:
            result = ed[0].minified()
            result["distance"] = int(ed[1] / 1000)
            event_dates_with_location.append(result)
        return event_dates_with_location
    else:
        return [e.minified() for e in event_dates]
