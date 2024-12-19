from psycopg2 import OperationalError
import time
import os
from flask.helpers import get_debug_flag
from pmapi.event.controllers import get_event_or_404
from pmapi.event.model import Event
from pmapi.event_artist.controllers import add_artists_to_date
from pmapi.event_artist.model import Artist
from pmapi.event_date.model import EventDate
from pmapi.event_review.model import EventReview
from pmapi.extensions import mail
from ffmpy import FFmpeg
from pmapi.services.goabase import GoabaseEventFetcher, fetch_events_from_goabase
from .config import DevConfig, ProdConfig
from requests.exceptions import RequestException
from pmapi.extensions import db
from pmapi.utils import SUPPORTED_LANGUAGES, get_description_translation, get_lineup_from_image, get_lineup_from_text
from flask import g


DEV_ENVIRON = get_debug_flag()
CONFIG = DevConfig if DEV_ENVIRON else ProdConfig

from pmapi.celery_worker import celery

@celery.task(ignore_result=True)
def background_send_mail(
    to, subject, content, content_type, from_=None, msg_type="unknown"
):
    result = mail.send(to, subject, content, content_type, from_)
    logging.info(
        "send.mail",
        to=to,
        subject=subject,
        status=result and "sent" or "failed",
        msg_type=msg_type,
    )
    return result


@celery.task()
def run_video_conversion(
    input_filepath,
    output_filepath,
    min_bitrate,
    target_bitrate,
    max_bitrate,
    width,
    height,
):
    ff = FFmpeg(
        executable="/usr/bin/ffmpeg",
        inputs={input_filepath: None},
        outputs={
            output_filepath: "-c:a libvorbis -c:v vp9 -b:v {0}k -minrate {1}k -maxrate {2}k \
             -quality good -speed 4 -c:a libvorbis -vf scale={3}x{4}".format(
                target_bitrate, min_bitrate, max_bitrate, width, height
            )
        },
    )
    ff.run()


@celery.task()
def get_video_thumbnail(
    input_filepath,
    thumb_out_filepath,
    poster_out_filepath,
    thumb_width=None,
    thumb_height=None,
):
    ff = FFmpeg(
        executable="/usr/bin/ffmpeg",
        inputs={input_filepath: None},
        outputs={
            thumb_out_filepath: "-ss 00:00:01.000 -vframes 1 -vf scale={0}x{1}".format(
                thumb_width, thumb_height
            )
        },
    )
    ff.run()
    ff = FFmpeg(
        executable="/usr/bin/ffmpeg",
        inputs={input_filepath: None},
        outputs={poster_out_filepath: "-ss 00:00:01.000 -vframes 1"},
    )
    ff.run()


@celery.task(autoretry_for=(RequestException, OperationalError), retry_backoff=True, retry_backoff_max=120, rate_limit="30/m"
)
def refresh_artist_info(artist_id):
    from pmapi.event_artist.controllers import refresh_info
    refresh_info(artist_id)

@celery.task(autoretry_for=(RequestException, OperationalError), retry_backoff=True, retry_backoff_max=120, rate_limit="30/m"
)
def update_event_translation(event_id):
    event = db.session.query(Event).filter(Event.id == event_id).first()
    if event:
        event.description_translations = update_translation_field(event.description_translations, event.description)
        event.full_description_translations = update_translation_field(event.full_description_translations, event.full_description)
        db.session.commit()
        db.session.close()

@celery.task(autoretry_for=(RequestException,OperationalError), retry_backoff=True, retry_backoff_max=120, rate_limit="30/m"
)
def update_event_date_translation(id):
    print('update_event_date_translation, ed id', id)
    event_date = db.session.query(EventDate).filter(EventDate.id == id).first()
    event_date.description_translations = update_translation_field(event_date.description_translations, event_date.description)
    db.session.commit()

@celery.task(autoretry_for=(RequestException,OperationalError), retry_backoff=True, retry_backoff_max=120, rate_limit="30/m"
)
def update_artist_translation(id):
    artist = db.session.query(Artist).filter(Artist.id == id).first()
    if (artist.disambiguation):
        artist.description_translations = update_translation_field(artist.disambiguation_translations, artist.disambiguation)
    if (artist.description):
        artist.description_translations = update_translation_field(artist.description_translations, artist.description)
    db.session.commit()


@celery.task(autoretry_for=(RequestException,OperationalError), retry_backoff=True, retry_backoff_max=120, rate_limit="30/m"
)
def update_review_translation(id):
    review = db.session.query(EventReview).filter(EventReview.id == id).first()
    review.text_translations = update_translation_field(review.text_translations, review.text)
    db.session.commit()


def update_translation_field(translation_field, input_text, onlyMissing=False):
    if translation_field is None:
        translation_field = {}

    for lang in SUPPORTED_LANGUAGES:
        if not onlyMissing or lang not in translation_field:
            translation_field[lang] = get_description_translation(input_text, lang)
            time.sleep(1.5)

    return translation_field



@celery.task(autoretry_for=(RequestException,OperationalError), retry_backoff=True, retry_backoff_max=120, rate_limit="30/m"
)
def get_lineup_from_image_and_text(event_id, lineup_text, lineup_image_url):
    event = get_event_or_404(event_id)
    next_ed = event.next_event()
    
    lineup = get_lineup_from_text(lineup_text)

    if not lineup or lineup and len(lineup) == 0:
        print('LINEUP getting from img')
        lineup = get_lineup_from_image(lineup_image_url)

    print('LINEUP result: ', lineup)

    if lineup: 
        add_artists_to_date(next_ed, lineup)
        db.session.commit()
    else:
        print('LINEUP not found for ' + event.name)

@celery.task(autoretry_for=(RequestException,OperationalError), retry_backoff=True, retry_backoff_max=120, rate_limit="30/m"
)
def fetch_goabase_events():
    fetch_events_from_goabase()

