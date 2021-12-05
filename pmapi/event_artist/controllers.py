import pytz
from datetime import datetime
from timezonefinder import TimezoneFinder
from sqlalchemy import and_

import time
import requests
from flask_login import current_user
from pmapi.extensions import db, activity_plugin
from .model import Artist, ArtistUrl, EventDateArtist

Activity = activity_plugin.activity_cls


def remove_artists_from_date(event_date, ed_artists):
    for artist in ed_artists:
        print(artist.get("id"))
        artist = (
            db.session.query(EventDateArtist)
            .filter(EventDateArtist.id == artist.get("id"))
            .first()
        )
        print(artist)
        db.session.delete(artist)
        # db.session.flush()
        # activity = Activity(verb=u"delete", object=artist, target=event_date.event)
        # db.session.add(activity)
    return


def update_artists(event_date, artists):
    for artist in artists:
        existing_record = (
            db.session.query(EventDateArtist)
            .filter(EventDateArtist.id == artist.get("id"))
            .first()
        )
        if existing_record:
            start_naive = artist.get("start_naive", None)
            if start_naive is not None:
                # get timezone of event_date
                if event_date.tz:
                    tz_obj = pytz.timezone(event_date.tz)
                else:
                    tf = TimezoneFinder()
                    tz = tf.timezone_at(
                        lng=event_date.location.lng, lat=event_date.location.lat
                    )
                    tz_obj = pytz.timezone(tz)

                # parse date string as naive datetime
                start_naive = datetime.strptime(
                    start_naive, "%Y-%m-%d %H:%M:%S"
                ).replace(second=0, microsecond=0, tzinfo=None)

                start_utc = tz_obj.localize(start_naive)
                start_utc = start_utc.astimezone(pytz.utc)
                start_utc = start_utc.replace(tzinfo=None)
                existing_record.start = start_utc
                existing_record.start_naive = start_naive
    return


def add_artists_to_date(event_date, artists):
    for artist in artists:
        existing_record = (
            db.session.query(EventDateArtist)
            .join(Artist)
            .filter(
                and_(
                    Artist.name == artist["name"],
                    EventDateArtist.event_date_id == event_date.id,
                )
            )
            .first()
        )
        if existing_record is None:
            print(artist)
            add_artist_to_date(event_date, **artist)


def add_artist_to_date(event_date, name, id=None, start_naive=None, **kwargs):

    artist = None
    start_utc = None
    print(name)
    print(kwargs)
    if id:  # mbid
        # music brainz search
        artist = get_artist_by_mbid(id)

        response = getArtistDetailsFromMusicBrainz(id)
        if response.status_code != 200:
            # wait and try again (musicbrainz api limited to one req/sec)
            time.sleep(1)
            response = getArtistDetailsFromMusicBrainz(id)

        print(response)
        response = response.json()
        print("json", response)
        area = response.get("area", None)
        if area:
            area = area.get("name", None)

        if artist is None:
            # maybe artist is already in db
            artist = get_artist_by_name(name)
            if artist is None:
                # create new record
                artist = Artist(
                    name=name,
                    disambiguation=response["disambiguation"],
                    area=area,
                    mbid=id,
                )
                db.session.add(artist)
                db.session.flush()
            else:
                # update existing manual entry to be music brainz entry
                artist.disambiguation = response["disambiguation"]
                artist.area = area
                artist.mbid = id
                db.session.flush()
        else:
            # update existing music brainz record with new data
            artist.disambiguation = response["disambiguation"]
            artist.area = area
            db.session.flush()

        # process artist URLs
        for relation in response["relations"]:
            # make sure urls are up to date
            url = (
                db.session.query(ArtistUrl)
                .filter(ArtistUrl.url == relation["url"]["resource"])
                .first()
            )
            if url is None:
                url = ArtistUrl(
                    artist=artist,
                    url=relation["url"]["resource"],
                    type=relation["type"],
                )
                db.session.add(url)
            else:
                url.artist = artist

    else:
        artist = get_artist_by_name(name)
        if artist is None:
            # create new artist record
            artist = Artist(name=name)
            db.session.add(artist)

    db.session.flush()

    if start_naive:
        # get timezone of event_date
        if event_date.tz:
            tz_obj = pytz.timezone(event_date.tz)
        else:
            tf = TimezoneFinder()
            tz = tf.timezone_at(
                lng=event_date.location.lng, lat=event_date.location.lat
            )
            tz_obj = pytz.timezone(tz)

        # parse date string as naive datetime
        start_naive = datetime.strptime(start_naive, "%Y-%m-%d %H:%M:%S").replace(
            second=0, microsecond=0, tzinfo=None
        )

        start_utc = tz_obj.localize(start_naive)
        start_utc = start_utc.astimezone(pytz.utc)
        start_utc = start_utc.replace(tzinfo=None)

    event_date_artist = EventDateArtist(
        artist=artist,
        event_date=event_date,
        creator=current_user,
        start=start_utc,
        start_naive=start_naive,
    )

    # db.session.add(event_date_artist)
    # db.session.flush()
    # activity = Activity(
    #     verb=u"create", object=event_date_artist, target=event_date.event
    # )
    # db.session.add(activity)

    return event_date_artist


def get_artist_by_name(name):
    return db.session.query(Artist).filter(Artist.name.ilike(name)).first()


def get_artist_by_mbid(mbid):
    return db.session.query(Artist).filter(Artist.mbid == mbid).first()


def getArtistDetailsFromMusicBrainz(mbid):
    response = requests.get(
        url="https://musicbrainz.org/ws/2/artist/" + mbid + "?inc=url-rels",
        headers={"Accept": "application/json"},
    )
    return response
