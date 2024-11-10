from datetime import time
from flask.helpers import get_debug_flag
import logging
from celery import Celery
from pmapi.extensions import mail
from ffmpy import FFmpeg
from flask.helpers import get_debug_flag
from .config import DevConfig
from .config import ProdConfig
from requests.exceptions import RequestException
from pmapi.extensions import db
from pmapi.utils import SUPPORTED_LANGUAGES, get_translation

DEV_ENVIRON = get_debug_flag()
CONFIG = DevConfig if DEV_ENVIRON else ProdConfig

celery = Celery(
    __name__,
    backend=CONFIG.CELERY_RESULT_BACKEND,
    broker=CONFIG.CELERY_BROKER_URL,
)

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


@celery.task(
    autoretry_for=(RequestException,), retry_backoff=True, retry_backoff_max=120, rate_limit="30/m"
)
def refresh_artist_info(artist_id):
    from pmapi.event_artist.controllers import refresh_info
    refresh_info(artist_id)
    db.session.close()  # close session so we don't have issues with celery workers

@celery.task(
    autoretry_for=(RequestException,), retry_backoff=True, retry_backoff_max=120, rate_limit="30/m"
)
def update_translation_field(obj, translation_field_name, input_text, onlyMissing=True):

    translation_field = obj.getattr(translation_field_name)
    if translation_field is None:
        translation_field = {}
        setattr(obj, translation_field_name, translation_field)

    for lang in SUPPORTED_LANGUAGES:
        if not onlyMissing or lang not in translation_field:
            translation_field[lang] = get_translation(input_text, lang, CONFIG.DIFY_TRANSLATE_TAG_KEY)
            time.sleep(1.5)
    print('updated translation field for ' + obj.__name__ + ' (id: ' + obj.get('id', None))
    print(translation_field)

    db.session.commit()
    db.session.close()
    return translation_field