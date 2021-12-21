import os
import uuid
import re
import subprocess
import base64
import json

from flask import current_app, flash
from PIL import Image
from mimetypes import guess_extension
from flask_login import current_user
from ffmpy import FFprobe
from datetime import datetime

# import magic

from .model import MediaItem
from pmapi.extensions import db, activity_plugin
from pmapi import exceptions as exc

import pmapi.event.controllers as events
import pmapi.tasks as tasks

Activity = activity_plugin.activity_cls


def delete_item(id):
    item = get_media_item_or_404(id)
    event = events.get_event_or_404(item.event_id)
    db.session.delete(item)

    # trigger event revision
    event.updated_at = datetime.utcnow()
    db.session.flush()

    activity = Activity(verb=u"delete", object=item, target=event)
    db.session.add(activity)
    db.session.commit()

    return "", 204


def update_item(id, **kwargs):
    item = get_media_item_or_404(id)
    if "caption" in kwargs:
        item.caption = kwargs.pop("caption")

    if "position" in kwargs:
        # reorder list and fix any errors in numbering
        item.event.media_items.reorder()
        event = events.get_event_or_404(item.event_id)
        position = kwargs.pop("position")
        event.media_items.pop(item.position)
        # add item to list again
        event.media_items.insert(position, item)
        item.event_id = event.id

        # trigger event revision
        event.updated_at = datetime.utcnow()
        db.session.flush()
        activity = Activity(verb=u"update", object=item, target=event)
        db.session.add(activity)

        # update
    db.session.commit()
    return item


def get_media_item_or_404(item_id):
    item = get_media_item_by_id(item_id)
    if item is None:
        msg = "No such item with id {}".format(item_id)
        raise exc.RecordNotFound(msg)
    return item


def get_media_item_by_id(item_id):
    return MediaItem.query.get(item_id)


def remove_all_media_from_event(event):
    for item in event.media_items:
        db.session.delete(item)
        db.session.flush()
        activity = Activity(verb=u"delete", object=item, target=event)
        db.session.add(activity)
    return


def add_media_to_artist(items, artist, creator=current_user):
    for i in items:
        file = i["base64File"]
        path = os.path.join(
            current_app.config["MEDIA_UPLOAD_FOLDER"] + str("artist/") + str(artist.id)
        )
        (
            thumb_filename,
            image_filename,
            video_low_filename,
            video_med_filename,
            video_high_filename,
            video_poster_filename,
            duration,
            type,
        ) = save_media_item(file, path)
        if thumb_filename:
            media_item = MediaItem(
                artist=artist,
                caption=i.get("caption", None),
                image_filename=image_filename,
                video_low_filename=video_low_filename,
                video_med_filename=video_med_filename,
                video_high_filename=video_high_filename,
                video_poster_filename=video_poster_filename,
                duration=duration,
                thumb_filename=thumb_filename,
                type=type,
                creator_id=creator.id,
            )
            db.session.add(media_item)
            db.session.flush()
            artist.media_items.append(media_item)
            # activity
            db.session.flush()
            activity = Activity(verb=u"create", object=media_item, target=artist)
            db.session.add(activity)

    db.session.commit()
    return artist.media_items


def add_media_to_event(items, event, event_date=None, creator=current_user):

    for i in items:
        file = i["base64File"]
        path = os.path.join(
            current_app.config["MEDIA_UPLOAD_FOLDER"] + str("event/") + str(event.id)
        )

        (
            thumb_filename,
            image_filename,
            video_low_filename,
            video_med_filename,
            video_high_filename,
            video_poster_filename,
            duration,
            type,
        ) = save_media_item(file, path)
        if thumb_filename:
            media_item = MediaItem(
                event=event,
                event_date=event_date,
                caption=i.get("caption", None),
                image_filename=image_filename,
                video_low_filename=video_low_filename,
                video_med_filename=video_med_filename,
                video_high_filename=video_high_filename,
                video_poster_filename=video_poster_filename,
                duration=duration,
                thumb_filename=thumb_filename,
                type=type,
                creator_id=creator.id,
            )
            db.session.add(media_item)
            db.session.flush()
            event.media_items.append(media_item)
            # activity
            db.session.flush()
            activity = Activity(verb=u"create", object=media_item, target=event)
            db.session.add(activity)

    db.session.commit()
    return event.media_items


def save_media_item(file, path):
    if not file:
        raise exc.InvalidAPIRequest("file required")

    # create the directory you want to save to
    if not (os.path.exists(path)):
        try:
            original_umask = os.umask(0)
            os.makedirs(path, mode=0o777)
        except Exception as e:
            print("error", e)
        finally:
            os.umask(original_umask)

    # mimetype = magic.from_buffer(open(file, "rb").read(2048), mime=True)
    mimetype = file[file.find("data:") + 5 : file.find(";base64,")]
    # the string generated by the client includes the mimetype
    # which ISNT in base64.
    # this gets the main base64 string
    base64_string = re.search(r"base64,(.*)", file).group(1)

    file_extension = guess_extension(mimetype)
    if file_extension == ".jpeg":
        file_extension = ".jpg"

    unique_filename = str(uuid.uuid4())

    thumb_filename = unique_filename + "_thumb" + file_extension
    filename = unique_filename + file_extension

    video_low_filename = None
    video_med_filename = None
    video_high_filename = None
    duration = None
    type = None

    if (
        mimetype == "video/mp4"
        or mimetype == "video/mpeg"
        or mimetype == "video/x-msvideo"
        or mimetype == "video/ogg"
        or mimetype == "video/webm"
        or mimetype == "video/3gpp"
        or mimetype == "video/avi"
    ):
        type = "video"
    elif (
        mimetype == "image/png"
        or mimetype == "image/gif"
        or mimetype == "image/jpeg"
        or mimetype == "image/jpg"
        or mimetype == "image/bmp"
        or mimetype == "image/webp"
    ):
        type = "image"

    if type == "image":

        with open(os.path.join(path, filename), "wb") as fh:
            fh.write(base64.b64decode(base64_string))

        img = Image.open(os.path.join(path, filename))

        if img.mode != "RGB":
            img = img.convert("RGB")

        img.thumbnail((512, 512), Image.ANTIALIAS)
        img.save(os.path.join(path, thumb_filename))

        return thumb_filename, filename, None, None, None, None, None, "image"

    elif type == "video":
        thumb_filename = unique_filename + "_thumb" + ".jpeg"
        video_poster_filename = unique_filename + "_poster" + ".jpeg"
        file_extension = ".webm"
        filepath = os.path.join(path, filename)
        # save a copy to work with
        with open(filepath, "wb") as fh:
            fh.write(base64.b64decode(base64_string))

        video_info = FFprobe(
            executable="/usr/bin/ffprobe",
            inputs={filepath: None},
            global_options=[
                "-v",
                "quiet",
                "-print_format",
                "json",
                "-show_format",
                "-show_streams",
            ],
        ).run(stdout=subprocess.PIPE)
        video_info = json.loads(video_info[0].decode("utf-8"))

        duration = int(float(video_info["format"]["duration"]))

        if duration / 60 > 20:  # in minutes
            raise exc.InvalidAPIRequest("Video must be shorter than 20 minutes")

        width = int(video_info["streams"][0]["width"])
        height = int(video_info["streams"][0]["height"])

        # create thumbnails
        thumb_width, thumb_height = get_new_video_dimensions(
            width, height, max_width=512, max_height=512
        )
        tasks.get_video_thumbnail(
            input_filepath=filepath,
            thumb_out_filepath=os.path.join(path, thumb_filename),
            poster_out_filepath=os.path.join(path, video_poster_filename),
            thumb_height=thumb_height,
            thumb_width=thumb_width,
        )

        # create lowres webm
        lowres_width, lowres_height = get_new_video_dimensions(
            width, height, max_width=854, max_height=480
        )
        video_low_filename = unique_filename + "_v_low" + file_extension

        tasks.run_video_conversion.delay(
            input_filepath=filepath,
            output_filepath=os.path.join(path, video_low_filename),
            min_bitrate=400,
            target_bitrate=600,
            max_bitrate=800,
            width=lowres_width,
            height=lowres_height,
        )

        if (width >= 1920 and height >= 1080) or (height >= 1920 and width >= 1080):
            midres_width, midres_height = get_new_video_dimensions(
                width, height, max_width=1920, max_height=1080
            )
            video_med_filename = unique_filename + "_v_med" + file_extension

            tasks.run_video_conversion.delay(
                input_filepath=filepath,
                output_filepath=os.path.join(path, video_med_filename),
                min_bitrate=600,
                target_bitrate=1000,
                max_bitrate=1200,
                width=midres_width,
                height=midres_height,
            )
            # save 4k copy
            if (width >= 3840 and height >= 2160) or (height >= 3840 and width >= 2160):
                highres_width, highres_height = get_new_video_dimensions(
                    width, height, max_width=3840, max_height=2160
                )
                video_high_filename = unique_filename + "_v_high" + file_extension
                tasks.run_video_conversion.delay(
                    input_filepath=filepath,
                    output_filepath=os.path.join(path, video_high_filename),
                    min_bitrate=1000,
                    target_bitrate=1500,
                    max_bitrate=2000,
                    width=highres_width,
                    height=highres_height,
                )

        return (
            thumb_filename,
            None,
            video_low_filename,
            video_med_filename,
            video_high_filename,
            video_poster_filename,
            duration,
            "video",
        )

    else:
        flash("No selected file")
        return None, None, None, None, None, None, None


def get_new_video_dimensions(width, height, max_width, max_height):
    width_ratio = max_width / width
    height_ratio = max_height / height
    # is it a portrait video?
    if height > width:
        width_ratio = max_height / width
        height_ratio = max_width / height

    best_ratio = min(width_ratio, height_ratio)
    new_width = width * best_ratio
    new_height = height * best_ratio

    return int(new_width), int(new_height)
