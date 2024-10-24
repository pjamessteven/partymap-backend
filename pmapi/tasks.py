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

DEV_ENVIRON = get_debug_flag()
CONFIG = DevConfig if DEV_ENVIRON else ProdConfig

celery = Celery(
    __name__,
    backend=CONFIG.CELERY_RESULT_BACKEND,
    broker=CONFIG.CELERY_BROKER_URL,
)


def configure_celery(app, celery):

    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


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
    autoretry_for=(RequestException,), retry_backoff=True, retry_backoff_max=120, rate_limit="1/s"
)
def refresh_artist_info(artist_id):
    DEV_ENVIRON = get_debug_flag()

    CONFIG = DevConfig if DEV_ENVIRON else ProdConfig

    import pmapi.application as application
    app = application.create_app(config=CONFIG)

    with app.app_context():
        from pmapi.event_artist.controllers import refresh_info
        refresh_info(artist_id)
        db.session.close()  # close session so we don't have issues with celery workers
