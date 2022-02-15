import logging
from pmapi.extensions import mail, celery
from ffmpy import FFmpeg
import pmapi.event_artist.controllers as artists
import pmapi.application as application
from .config import DevConfig
from .config import ProdConfig
from flask.helpers import get_debug_flag

DEV_ENVIRON = get_debug_flag()

CONFIG = DevConfig if DEV_ENVIRON else ProdConfig


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


@celery.task()
def refresh_artist_info(artist_id):
    app = application.create_app(config=CONFIG, app_name="PARTYMAP")
    with app.app_context():
        artists.refresh_info(artist_id)
