import pytz
from datetime import datetime
from pmapi.media_item.controllers import add_media_to_artist
from timezonefinder import TimezoneFinder
from sqlalchemy import cast, or_, and_, desc
from geoalchemy2 import func, Geography
from pmapi import exceptions as exc, user
import hashlib
import base64
import time
import requests
from requests.exceptions import RequestException
from flask_login import current_user
from pmapi.extensions import db, activity_plugin
from .model import Artist, ArtistUrl, EventDateArtist, ArtistTag
from pmapi.event.model import Event
from pmapi.event_date.model import EventDate
from pmapi.event_tag.model import Tag
from pmapi.event_location.model import EventLocation
import logging
import difflib
from pmapi.config import BaseConfig
from pmapi.hcaptcha.controllers import validate_hcaptcha

from pmapi.common.controllers import paginated_results
from pmapi.tasks import refresh_artist_info, update_artist_translation

Activity = activity_plugin.activity_cls

TIMEOUT = 5

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
            raise exc.InvalidAPIRequest(
                "lat and lng are required for nearby search.")

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

    elif "bounds" in kwargs:
        query = (
            query
            .join(Event, EventDate.event_id == Event.id)
            .join(EventLocation, EventDate.location_id == EventLocation.id)
        )
        bounds = kwargs.get("bounds")

        northEast = bounds["_northEast"]
        southWest = bounds["_southWest"]

        query = query.filter(
            and_(
                or_(
                    and_(
                        southWest["lat"] < northEast["lat"],
                        EventLocation.lat.between(
                            southWest["lat"], northEast["lat"]),
                    ),
                    and_(
                        northEast["lat"] < southWest["lat"],
                        EventLocation.lat.between(
                            northEast["lat"], southWest["lat"]),
                    ),
                ),
                # match lng
                or_(
                    and_(
                        southWest["lng"] < northEast["lng"],
                        EventLocation.lng.between(
                            southWest["lng"], northEast["lng"]),
                    ),
                    and_(
                        northEast["lng"] < southWest["lng"],
                        EventLocation.lng.between(
                            northEast["lng"], southWest["lng"]),
                    ),
                ),
            )
        )

    if kwargs.get("query", None) is not None:
        search = "%{}%".format(kwargs.pop("query"))
        query = query.filter(Artist.name.ilike(search))

    if kwargs.pop("sort") == "event_count":
        # IDK why but if this order_by filter is passed to paginated_results it fucks up hard
        # possibly doesn't exist on model because it's a dynamic field?
        # ** all is well **
        if kwargs.pop("desc") is True:
            query = query.order_by(desc(Artist.event_count))
        else:
            query = query.order_by(Artist.event_count)

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
        if artist:
            db.session.delete(artist)
            db.session.flush()  
            activity = Activity(verb=u"delete", object=artist, target=event_date)
            db.session.add(activity)
    return


def update_artist(id, **kwargs):
    creator = kwargs.pop("creator", None)
    artist = get_artist_or_404(id)

    urls_to_add = kwargs.get("add_urls", None)
    urls_to_remove = kwargs.get("remove_urls", None)
    tags_to_add = kwargs.get("add_tags", None)
    tags_to_remove = kwargs.get("remove_tags", None)
    media_items = kwargs.get("media_items", None)

    for key, value in kwargs.items():
        # update basic values
        if hasattr(artist, key):
            setattr(artist, key, value)

    if urls_to_add:
        for url in urls_to_add:
            add_artist_url(url.get("url"), url.get("type"), artist)

    if urls_to_remove:
        for url_id in urls_to_remove:
            delete_artist_url(url_id)

    if tags_to_add:
        add_tags_to_artist(tags_to_add, artist)

    if tags_to_remove:
        remove_tags_from_artist(tags_to_remove, artist)

    if media_items:
        add_media_to_artist(media_items, artist, creator=creator)

    db.session.flush()

    activity = Activity(verb=u"update", object=artist, target=artist)
    db.session.add(activity)
    db.session.commit()

    return artist


def update_artists_of_date(event_date, artists):
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


def add_artist(name, mbid=None):
    # create new record
    artist = Artist(
        name=name,
        mbid=mbid,
    )
    db.session.add(artist)
    db.session.flush()
    refresh_artist_info.delay(artist.id)

    return artist


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

            if artist is None:
                artist = add_artist(name, mbid)

            else:
                # update existing artist with mbid
                artist.mbid = mbid
                db.session.flush()
                refresh_artist_info.delay(artist.id)

    elif id:
        artist = get_artist_by_id(id)
    else:
        artist = get_artist_by_name(name)
        if artist is None:
            # create new artist record
            artist = add_artist(name)

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

    db.session.add(event_date_artist)
    db.session.flush()
    activity = Activity(
         verb=u"create", object=event_date_artist, target=event_date
    )
    db.session.add(activity)

    return event_date_artist


def save_artist_image_from_wikimedia_url(url, artist):
    try:
        headers = {
            "Accept": "image/*",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:95.0) Gecko/20100101 Firefox/95.0",
        }
        r = requests.get(url, headers=headers, timeout=TIMEOUT)
    except RequestException as e:
        logging.error(
            "event_artist.save_artist_image_from_wikimedia_url.request_error",
            status_code="",
            error_body="",  # TODO: proper status code here
            exception=e,
        )

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
        add_media_to_artist(items, artist)
    except Exception:
        logging.error(
            "event_artist.save_artist_image_from_wikimedia_url.add_media_to_artist",
        )


def get_artist_details_from_music_brainz(mbid, attempt=5):
    if attempt > 0:
        # wait  (musicbrainz api limited to one req/sec)
        try:
            response = requests.get(
                url="https://musicbrainz.org/ws/2/artist/"
                + mbid
                + "?inc=url-rels&fmt=json",
                headers={"Accept": "application/json"},
                timeout=TIMEOUT,
            )
        except RequestException as e:
            logging.error(
                "event_artist.get_artist_details_from_music_brainz.request_error",
                status_code=response.status_code,
                error_body="", 
                exception=e,
            )

        if response.status_code != 200:
            time.sleep(2)
            return get_artist_details_from_music_brainz(mbid, attempt-1)
        return response.json()
    
    logging.error(
        "event_artist.get_artist_details_from_music_brainz.max_retries_reached",
        status_code=response.status_code,
        error_body="max retries reached for getting artist details " + mbid, 
        exception=e,
    )

def get_artist_details_from_last_fm(mbid, retries=5):
    if retries > 0:
        url = (
            "http://ws.audioscrobbler.com/2.0/?method=artist.getinfo&api_key="
            + BaseConfig.LAST_FM_API_KEY
            + "&mbid="
            + mbid
            + "&format=json"
        )
        try:
            response = requests.get(
                url=url, headers={"Accept": "application/json"}, timeout=TIMEOUT
            )
        except RequestException as e:
            logging.error(
                "event_artist.get_artist_details_from_last_fm.request_error",
                status_code="",
                error_body=response.status_code,  # TODO: proper status code here
                exception=e,
            )

        if response.status_code != 200:
            # wait and try again (last.fm api limited to one req/sec)
            time.sleep(2)
            return get_artist_details_from_last_fm(mbid, retries-1)

        response = response.json()
        bio = response.get("artist", {}).get("bio", {}).get("content", None)
        tags = []
        for tag in response.get("artist", {}).get("tags", {}).get("tag", []):
            tags.append(tag.get("name"))

        return bio, tags
    
    logging.error(
        "event_artist.get_artist_details_from_music_brainz.max_retries_reached",
        status_code=response.status_code,
        error_body="max retries reached for getting artist details " + mbid, 
        exception=e,
    )


def refresh_spotify_data_for_artist(artist):
    # GET ACCESS TOKEN
    AUTH_URL = "https://accounts.spotify.com/api/token"
    try:
        auth_response = requests.post(
            AUTH_URL,
            {
                "grant_type": "client_credentials",
                "client_id": BaseConfig.SPOTIFY_CLIENT_ID,
                "client_secret": BaseConfig.SPOTIFY_API_KEY,
            },
        )
    except RequestException as e:
        logging.error(
            "event_artist.refresh_spotify_data_for_artist.auth_token_request_error",
            status_code="",
            error_body="",  # TODO: proper status code here
            exception=e,
        )

    auth_response_data = auth_response.json()

    # save the access token
    access_token = auth_response_data["access_token"]
    headers = {
        "Authorization": "Bearer {token}".format(token=access_token),
        "Accept": "application/json",
    }
    url = "https://api.spotify.com/v1/search?type=artist&q=" + artist.name

    try:
        response = requests.get(url=url, headers=headers, timeout=TIMEOUT)
    except RequestException as e:
        logging.error(
            "event_artist.refresh_spotify_data_for_artist.main_request_error",
            status_code="",
            error_body="",  # TODO: proper status code here
            exception=e,
        )

    response = response.json()
    items = response.get("artists", {}).get("items", [])

    if len(items) > 0:
        # try to get the right artist from the deezer response
        # make sure artist name exists in response
        spotify_artist_names = []
        for item in items:
            spotify_artist_names.append(item.get("name"))
        close_matches = difflib.get_close_matches(
            artist.name, spotify_artist_names)
        spotify_artist_name = None
        spotify_artist = None
        if len(close_matches) > 0:
            spotify_artist_name = close_matches[0]
        # get the right artist from response
        for item in sorted(items, key=lambda d: d.get("popularity"), reverse=True):
            if item.get("name") == spotify_artist_name:
                spotify_artist = item
                break

        # get artist image
        if spotify_artist:
            # get tags too, why not
            if len(spotify_artist.get("genres", [])) > 0:
                add_tags_to_artist(spotify_artist.get("genres"), artist, False)

            # delete existing spotify url
            for url in artist.urls:
                if "spotify" in url.url.lower():
                    db.session.delete(url)

            # save url
            url = spotify_artist.get("external_urls", {}).get("spotify", None)
            if url:
                add_artist_url(url, "spotify", artist)

            # save popularity
            artist.popularity = spotify_artist.get("popularity", 0)

            # now save image
            images = spotify_artist.get("images")
            if len(images) > 0:
                # sort images by biggest first
                images_sorted = sorted(
                    images, key=lambda d: d.get("height"), reverse=True
                )
                image_url = images_sorted[0].get("url")
                try:
                    headers = {
                        "Accept": "image/*",
                        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:95.0) Gecko/20100101 Firefox/95.0",
                    }
                    r = requests.get(
                        image_url, headers=headers, timeout=TIMEOUT)
                except RequestException as e:
                    logging.error(
                        "event_artist.refresh_spotify_data_for_artist.image_request_error",
                        status_code="",
                        error_body="",  # TODO: proper status code here
                        exception=e,
                    )
                    print("error getting artist image from spotify")
                # add to db
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
                        "event_artist.refresh_spotify_data_for_artist.base_64_encode",
                    )
                    print("error encoding spotify artist image as uri")
                items = [
                    {
                        "base64File": uri,
                        "caption": "Artist image from Spotify",
                    }
                ]
                try:
                    add_media_to_artist(items, artist)
                except Exception:
                    logging.error(
                        "event_artist.refresh_spotify_data_for_artist.add_media_to_artist",
                    )
                return True

    return False  # couldn't get image


def get_artist_image_from_deezer(artist):
    # search for artist
    url = (
        'https://api.deezer.com/search/artist?q=artist:"'
        + artist.name
        + '"&output=json'
    )
    try:
        response = requests.get(
            url=url, headers={"Accept": "application/json"}, timeout=TIMEOUT
        )
    except RequestException as e:
        logging.error(
            "event_artist.get_artist_image_from_deezer.search_request_error",
            status_code="",
            error_body="",  # TODO: proper status code here
            exception=e,
        )

    response = response.json()
    response = response.get("data", None)

    # try to get the right artist from the deezer response
    # make sure artist name exists in response
    deezer_artist_names = []
    for item in response:
        deezer_artist_names.append(item.get("name"))
    close_matches = difflib.get_close_matches(artist.name, deezer_artist_names)
    deezer_artist_name = None
    deezer_artist = None
    if len(close_matches) > 0:
        deezer_artist_name = close_matches[0]
    # get the right artist from response
    for item in response:
        if item.get("name") == deezer_artist_name:
            deezer_artist = item
            break

    if deezer_artist:
        deezer_artist_id = deezer_artist.get("id")
        # get artist object
        url = "https://api.deezer.com/artist/" + str(deezer_artist_id)
        response = requests.get(
            url=url, headers={"Accept": "application/json"}, timeout=TIMEOUT
        )
        response = response.json()
        img_url = response.get("picture_xl")
        try:
            headers = {
                "Accept": "image/*",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:95.0) Gecko/20100101 Firefox/95.0",
            }
            r = requests.get(img_url, headers=headers, timeout=TIMEOUT)

        except RequestException as e:
            logging.error(
                "event_artist.get_artist_image_from_deezer.artist_request_error",
                status_code="",
                error_body="",  # TODO: proper status code here
                exception=e,
            )
            print("error getting artist image from deezer")
        # add to db
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
                "event_artist.get_artist_image_from_deezer.base_64_encode",
            )
            print("error encoding deezer artist image as uri")
        items = [
            {
                "base64File": uri,
                "caption": "Artist image from Deezer",
            }
        ]
        try:
            add_media_to_artist(items, artist)
        except Exception:
            logging.error(
                "event_artist.get_artist_image_from_deezer.add_media_to_artist",
            )


def add_tags_to_artist(tags, artist, activity=True):
    for t in tags:
        # check if tag is already in db
        if db.session.query(Tag).filter(Tag.tag == t.lower()).count():
            tag = db.session.query(Tag).filter(Tag.tag == t.lower()).one()
        else:
            tag = Tag(tag=t.lower())

        existing_tag = (
            db.session.query(ArtistTag)
            .filter(and_(ArtistTag.tag_id == tag.tag, ArtistTag.artist_id == artist.id))
            .first()
        )
        # check if artist already has tag
        if existing_tag is None:
            at = ArtistTag(tag=tag, artist=artist)
            db.session.add(at)
            if activity:
                # add activity
                db.session.flush()
                activity = Activity(verb=u"create", object=at, target=artist)
                db.session.add(activity)

    return tags


def remove_tags_from_artist(tags, artist, activity=True):
    for t in tags:
        existing_tag = (
            db.session.query(ArtistTag)
            .filter(and_(ArtistTag.tag_id == t, ArtistTag.artist_id == artist.id))
            .first()
        )
        # check if artist already has tag
        if existing_tag:
            db.session.delete(existing_tag)
            # add activity
            db.session.flush()
            if activity:
                activity = Activity(
                    verb=u"delete", object=existing_tag, target=artist)
                db.session.add(activity)

    return


def add_musicbrainz_urls_to_artist(relations, artist):
    # process artist URLs
    for relation in relations:
        url = relation.get("url", {}).get("resource")
        # make sure urls are up to date
        artist_url = db.session.query(ArtistUrl).filter(
            ArtistUrl.url == url).first()
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
                        db.session.query(ArtistUrl).filter(
                            ArtistUrl.url == url).first()
                    )
                    if artist_url is None:
                        # add image as media item if it's not already in db
                        save_artist_image_from_wikimedia_url(url, artist)

            if artist_url is None:
                add_artist_url(url, type, artist, False)
        else:
            artist_url.artist = artist

    db.session.flush()
    return artist


def add_artist_url(url, type, artist, activity=True):
    # need to check twice because of artist image url
    artist_url = ArtistUrl(
        artist=artist,
        url=url,
        type=type,
    )
    db.session.add(artist_url)
    if activity:
        # activity
        activity = Activity(verb=u"create", object=artist_url, target=artist)
        db.session.add(activity)

    db.session.flush()
    return artist_url


def delete_artist_url(id, activity=True):
    url = ArtistUrl.query.get(id)
    artist = get_artist_by_id(url.artist_id)
    if url is not None:
        db.session.delete(url)
        db.session.flush()
        if activity:
            # activity
            activity = Activity(verb=u"delete", object=url, target=artist)
            db.session.add(activity)

    db.session.flush()


def delete_artist(id):
    artist = get_artist_or_404(id)
    if artist.artist_tags:
        for tag in artist.artist_tags:
            db.session.delete(tag)
    if artist.artist_urls:
        for url in artist.artist_urls:
            db.session.delete(url)
    if artist.suggestions:
        for suggestion in artist.suggestions:
            db.session.delete(suggestion)
    if artist.media_items:
        for media_item in artist.media_items:
            db.session.delete(media_item)
    db.session.flush()

    db.session.delete(artist)
    db.session.commit()
    db.session.flush()

def refresh_info(id):

    artist = get_artist_or_404(id)

    if artist.mbid:

        # music brainz search
        musicbrainz_response = get_artist_details_from_music_brainz(
            artist.mbid)

        # last.fm search
        lastfm_bio, lastfm_tags = get_artist_details_from_last_fm(artist.mbid)

        area = musicbrainz_response.get("area", None)
        if area:
            area = area.get("name", None)

        # update artist
        artist.disambiguation =  musicbrainz_response.get("disambiguation", None)
        artist.description = lastfm_bio
        artist.area = area
        if lastfm_tags and len(lastfm_tags) > 0:
            add_tags_to_artist(lastfm_tags, artist, False)

        if musicbrainz_response.get("relations", None):
            add_musicbrainz_urls_to_artist(
                musicbrainz_response["relations"], artist)

    # get images from external services
    # only use deezer as fallback

    for image in artist.media_items:
        if "Spotify" in image.caption:
            db.session.delete(image)
        if "Deezer" in image.caption:
            db.session.delete(image)
    db.session.flush()

    spotify_image_found = refresh_spotify_data_for_artist(artist)
    if not spotify_image_found:
        # get deezer image if spotify image doesn't exist
        get_artist_image_from_deezer(artist)

    db.session.commit()

    update_artist_translation.delay(artist.id)

    return artist
