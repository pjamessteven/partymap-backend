from psycopg2 import OperationalError
import time
import os
from flask.helpers import get_debug_flag
import logging
from pmapi.event.model import Event
from pmapi.event_artist.model import Artist
from pmapi.event_date.model import EventDate
from pmapi.event_review.model import EventReview
from pmapi.extensions import mail, celery
from ffmpy import FFmpeg
from .config import DevConfig
from .config import ProdConfig
from requests.exceptions import RequestException
from pmapi.extensions import db
from pmapi.utils import SUPPORTED_LANGUAGES, get_translation
from flask import g

DEV_ENVIRON = get_debug_flag()
CONFIG = DevConfig if DEV_ENVIRON else ProdConfig

def _create_app():
    from pmapi.application import create_app
    return create_app(config=CONFIG)


@celery.task(ignore_result=True)
def background_send_mail(
    to, subject, content, content_type, from_=None, msg_type="unknown"
):
    g.celery_task = True  # Use custom_sqlalchemy scoped session
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
    g.celery_task = True  # Use custom_sqlalchemy scoped session
    from pmapi.event_artist.controllers import refresh_info
    refresh_info(artist_id)

@celery.task(autoretry_for=(RequestException, OperationalError), retry_backoff=True, retry_backoff_max=120, rate_limit="30/m"
)
def update_event_translation(event_id):
    g.celery_task = True  # Use custom_sqlalchemy scoped session
    event = db.session.query(Event).filter(Event.id == event_id).first()
    event.description_translations = update_translation_field(event.description_translations, event.description)
    event.full_description_translations = update_translation_field(event.full_description_translations, event.full_description)
    db.session.commit()
    db.session.close()

@celery.task(autoretry_for=(RequestException,OperationalError), retry_backoff=True, retry_backoff_max=120, rate_limit="30/m"
)
def update_event_date_translation(id):
    g.celery_task = True  # Use custom_sqlalchemy scoped session
    event_date = db.session.query(EventDate).filter(EventDate.id == id).first()
    event_date.description_translations = update_translation_field(event_date.description_translations, event_date.description)
    db.session.commit()

@celery.task(autoretry_for=(RequestException,OperationalError), retry_backoff=True, retry_backoff_max=120, rate_limit="30/m"
)
def update_artist_translation(id):
    g.celery_task = True  # Use custom_sqlalchemy scoped session
    artist = db.session.query(Artist).filter(Artist.id == id).first()
    if (artist.disambiguation):
        artist.description_translations = update_translation_field(artist.disambiguation_translations, artist.disambiguation)
    if (artist.description):
        artist.description_translations = update_translation_field(artist.description_translations, artist.description)
    db.session.commit()


@celery.task(autoretry_for=(RequestException,OperationalError), retry_backoff=True, retry_backoff_max=120, rate_limit="30/m"
)
def update_review_translation(id):
    g.celery_task = True  # Use custom_sqlalchemy scoped session
    review = db.session.query(EventReview).filter(EventReview.id == id).first()
    review.text_translations = update_translation_field(review.text_translations, review.text)
    db.session.commit()



def update_translation_field(translation_field, input_text, onlyMissing=False):
    if translation_field is None:
        translation_field = {}

    for lang in SUPPORTED_LANGUAGES:
        if not onlyMissing or lang not in translation_field:
            translation_field[lang] = get_translation(input_text, lang, CONFIG.DIFY_TRANSLATE_KEY)
            time.sleep(1.5)

    return translation_field