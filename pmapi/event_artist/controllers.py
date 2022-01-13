import pytz
from datetime import datetime
from timezonefinder import TimezoneFinder
from sqlalchemy import cast, or_, and_, desc
from geoalchemy2 import func, Geography
from pmapi import exceptions as exc
import hashlib
import base64
import time
import requests
from flask_login import current_user
from pmapi.extensions import db, activity_plugin
from .model import Artist, ArtistUrl, EventDateArtist, ArtistTag
from pmapi.event_date.model import EventDate
from pmapi.event_tag.model import Tag
from pmapi.event_location.model import EventLocation
import logging
from pmapi.config import BaseConfig

from pmapi.common.controllers import paginated_results
import pmapi.media_item.controllers as media_items

Activity = activity_plugin.activity_cls


def get_artist_or_404(id):
    artist = get_artist(id)
    if not artist:
        msg = "No such artist with id {}".format(id)
        raise exc.RecordNotFound(msg)
    return artist


def get_artist(id):
    return Artist.query.get(id)


def get_artists(**kwargs):

    query = db.session.query(Artist)

    if "date_min" in kwargs:
        query = query.join(EventDateArtist).join(EventDate)
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
    if "radius" and "location" in kwargs:
        radius = kwargs.get("radius")
        location = kwargs.get("location")
        lat = float(location["lat"])
        lng = float(location["lng"])
        if lat is None or lng is None:
            raise exc.InvalidAPIRequest("lat and lng are required for nearby search.")

        query = query.join(EventLocation)
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

    if kwargs.get("query", None) is not None:
        search = "%{}%".format(kwargs.pop("query"))
        query = query.filter(Artist.name.ilike(search))

    query = query.order_by(desc(Artist.event_count))

    return paginated_results(Artist, query=query, **kwargs)


def get_artist_by_name(name):
    search = "%{}%".format(name)
    return db.session.query(Artist).filter(Artist.name.ilike(search)).first()


def get_artist_by_exact_name(name):
    return (
        db.session.query(Artist)
        .filter(func.lower(Artist.name) == func.lower(name))
        .first()
    )


def get_artist_by_mbid(mbid):
    return db.session.query(Artist).filter(Artist.mbid == mbid).first()


def get_artist_by_id(id):
    return db.session.query(Artist).filter(Artist.id == id).first()


def remove_artists_from_date(event_date, ed_artists):
    for artist in ed_artists:
        artist = (
            db.session.query(EventDateArtist)
            .filter(EventDateArtist.id == artist.get("id"))
            .first()
        )
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
                    Artist.name == artist.get("name"),
                    EventDateArtist.event_date_id == event_date.id,
                )
            )
            .first()
        )
        if existing_record is None:
            add_artist_to_date(event_date, **artist)


def add_artist_to_date(
    event_date, name, id=None, mbid=None, stage=None, start_naive=None, **kwargs
):

    artist = None
    start_utc = None

    if mbid:  # mbid
        # check if artist already exists
        artist = get_artist_by_mbid(mbid)

        if artist is None:
            # maybe artist is already in db
            artist = get_artist_by_exact_name(name)

            # music brainz search
            musicbrainz_response = getArtistDetailsFromMusicBrainz(mbid)

            # last.fm search
            lastfm_bio, lastfm_tags = getArtistDetailsFromLastFm(mbid)

            area = musicbrainz_response.get("area", None)
            if area:
                area = area.get("name", None)

            if artist is None:
                # create new record
                artist = Artist(
                    name=name,
                    disambiguation=musicbrainz_response["disambiguation"],
                    description=lastfm_bio,
                    area=area,
                    mbid=mbid,
                )
                db.session.add(artist)
                db.session.flush()
            else:
                # update existing manual entry to be music brainz entry
                artist.disambiguation = musicbrainz_response["disambiguation"]
                artist.description = lastfm_bio
                artist.area = area
                artist.mbid = mbid
                db.session.flush()

            if lastfm_tags and len(lastfm_tags) > 0:
                add_tags_to_artist(lastfm_tags, artist)

            if musicbrainz_response["relations"]:
                add_urls_to_artist(musicbrainz_response["relations"], artist)

    elif id:
        artist = get_artist_by_id(id)
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
        stage=stage,
        event_date=event_date,
        creator_id=current_user.id,
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


def save_artist_image_from_wikimedia_url(url, artist):
    try:
        headers = {
            "Accept": "image/*",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:95.0) Gecko/20100101 Firefox/95.0",
        }
        r = requests.get(url, headers=headers)
    except requests.exceptions.RequestException as e:
        logging.error(
            "event_artist.save_artist_image_from_wikimedia_url.request_error",
            status_code=r.status_code,
            error_body=r.body,
            exception=e,
        )
        print("error getting artist image")
    print(r)
    print(r.headers)
    print(url)
    try:
        uri = (
            "data:"
            + r.headers["Content-Type"]
            + ";"
            + "base64,"
            + base64.b64encode(r.content).decode("utf-8")
        )
    except Exception:
        logging.error(
            "event_artist.save_artist_image_from_wikimedia_url.base_64_encode",
        )
        print("error encoding artist image as uri")
    items = [
        {
            "base64File": uri,
            "caption": "Artist image from wikimedia under the Creative Commons Attribution 2.0 Generic license. ",
        }
    ]
    try:
        media_items.add_media_to_artist(items, artist)
    except Exception:
        logging.error(
            "event_artist.get_image_from_url_base64_encode.add_media_to_artist",
        )


def getArtistDetailsFromMusicBrainz(mbid):
    response = requests.get(
        url="https://musicbrainz.org/ws/2/artist/" + mbid + "?inc=url-rels&fmt=json",
        headers={"Accept": "application/json"},
    )
    if response.status_code != 200:
        print("status code", response.status_code)
        # wait and try again (musicbrainz api limited to one req/sec)
        time.sleep(1)
        return getArtistDetailsFromMusicBrainz(mbid)
    return response.json()


def getArtistDetailsFromLastFm(mbid):
    url = (
        "http://ws.audioscrobbler.com/2.0/?method=artist.getinfo&api_key="
        + BaseConfig.LAST_FM_API_KEY
        + "&mbid="
        + mbid
        + "&format=json"
    )
    response = requests.get(
        url=url,
        headers={"Accept": "application/json"},
    )
    if response.status_code != 200:
        print("status code", response.status_code)
        # wait and try again (last.fm api limited to one req/sec)
        time.sleep(1)
        return getArtistDetailsFromLastFm(mbid)

    response = response.json()
    bio = response.get("artist", {}).get("bio", {}).get("content", None)
    tags = []
    for tag in response.get("artist", {}).get("tags", {}).get("tag", []):
        tags.append(tag.get("name"))

    return bio, tags


def add_tags_to_artist(tags, artist):
    for t in tags:
        print(t)

        tag = Tag(tag=t)
        # check if tag is already in db
        if db.session.query(Tag).filter(Tag.tag == t).count():
            tag = db.session.query(Tag).filter(Tag.tag == t).one()

        existing_tag = (
            db.session.query(ArtistTag)
            .filter(and_(ArtistTag.tag_id == tag.tag, ArtistTag.artist_id == artist.id))
            .first()
        )
        # check if artist already has tag
        if existing_tag is None:
            at = ArtistTag(tag=tag, artist=artist)
            db.session.add(at)
            # add activity
            db.session.flush()
            activity = Activity(verb=u"create", object=at, target=artist)
            db.session.add(activity)
        print(tag)

    return tags


def add_urls_to_artist(relations, artist):
    # process artist URLs
    for relation in relations:
        url = relation.get("url", {}).get("resource")
        # make sure urls are up to date
        artist_url = db.session.query(ArtistUrl).filter(ArtistUrl.url == url).first()
        if artist_url is None:
            # create new url entry
            type = relation.get("type")
            if type == "image":
                # if it's a wikimedia image, do stuff

                if "https://commons.wikimedia.org/wiki/File:" in url:
                    # get a proper image url out of this
                    filename = url.split("File:")[1]
                    md5 = hashlib.md5(filename.encode("utf-8")).hexdigest()
                    weirdPathString = md5[0:1] + "/" + md5[0:2] + "/"
                    url = (
                        "https://upload.wikimedia.org/wikipedia/commons/"
                        + weirdPathString
                        + filename
                    )
                    # check that image url not already in DB
                    artist_url = (
                        db.session.query(ArtistUrl).filter(ArtistUrl.url == url).first()
                    )
                    if artist_url is None:
                        # add image as media item if it's not already in db
                        save_artist_image_from_wikimedia_url(url, artist)

            if artist_url is None:
                # need to check twice because of artist image url
                artist_url = ArtistUrl(
                    artist=artist,
                    url=url,
                    type=type,
                )
                db.session.add(artist_url)
        else:
            artist_url.artist = artist

    db.session.flush()
    return artist


def refresh_info(id):
    artist = get_artist_or_404(id)

    if not artist.mbid:
        raise exc.InvalidAPIRequest(
            "This artist is not in the Musicbrainz or Last.fm databases"
        )

    # music brainz search
    musicbrainz_response = getArtistDetailsFromMusicBrainz(artist.mbid)

    # last.fm search
    lastfm_bio, lastfm_tags = getArtistDetailsFromLastFm(artist.mbid)

    area = musicbrainz_response.get("area", None)
    if area:
        area = area.get("name", None)

    # update artist
    artist.disambiguation = musicbrainz_response["disambiguation"]
    artist.description = lastfm_bio
    artist.area = area

    if lastfm_tags and len(lastfm_tags) > 0:
        add_tags_to_artist(lastfm_tags, artist)

    if musicbrainz_response["relations"]:
        add_urls_to_artist(musicbrainz_response["relations"], artist)

    db.session.commit()
    return artist
