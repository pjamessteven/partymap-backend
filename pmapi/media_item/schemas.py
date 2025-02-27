from marshmallow import fields
from marshmallow import Schema
from pmapi.common.schemas import PaginatedSchema
from flask import current_app
import os
from typemallow2 import ts_interface
from pprint import pprint

@ts_interface
class MediaItemUploadSchema(Schema):
    caption = fields.Str(required=False, allow_none=True)
    base64File = fields.Str(required=False) # upload image 
    url = fields.Str(required=False) # or alternatively specify URL to get from
    mimeType = fields.Str(required=False)
    fileName = fields.Str(required=False)
    
@ts_interface()
class MediaItemSchema(Schema):
    id = fields.Int()
    attributes = fields.Dict()
    creator = fields.Nested("UserSchema", only=["username"])
    created_at = fields.DateTime()
    filename = fields.Str()
    position = fields.Int()
    duration = fields.Int()
    caption = fields.Str()
    type = fields.Str()
    image_url = fields.Function(
        lambda obj: generate_filepath(obj, obj.image_filename)
        if obj.image_filename
        else None
    )
    image_med_url = fields.Function(
        lambda obj: generate_filepath(obj, obj.image_med_filename)
        if obj.image_med_filename
        else None
    )
    v_low_url = fields.Function(
        lambda obj: generate_filepath(obj, obj.video_low_filename)
        if obj.video_low_filename
        else None
    )
    v_med_url = fields.Function(
        lambda obj: generate_filepath(obj, obj.video_med_filename)
        if obj.video_med_filename
        else None
    )
    v_high_url = fields.Function(
        lambda obj: generate_filepath(obj, obj.video_high_filename)
        if obj.video_high_filename
        else None
    )
    thumb_url = fields.Function(
        lambda obj: generate_filepath(obj, obj.thumb_filename)
        if obj.thumb_filename
        else None
    )
    thumb_xs_url = fields.Function(
        lambda obj: generate_filepath(obj, obj.thumb_xs_filename)
        if obj.thumb_xs_filename
        else None
    )
    thumb_xxs_url = fields.Function(
        lambda obj: generate_filepath(obj, obj.thumb_xxs_filename)
        if obj.thumb_xxs_filename
        else None
    )
    poster_url = fields.Function(
        lambda obj: generate_filepath(obj, obj.video_poster_filename)
        if obj.video_poster_filename
        else None
    )


@ts_interface()
class MediaItemVersionSchema(Schema):
    changeset = fields.Dict()
    thumb_url = fields.Function(
        lambda obj: generate_filepath(obj, obj.thumb_filename)
        if obj.thumb_filename
        else None
    )
    id = fields.UUID()
    caption = fields.Str()
    type = fields.Str()
    # previous = fields.Nested("MediaItemVersionSchema", exclude=["previous"])
    index = fields.Integer()
    transaction = fields.Nested("TransactionSchema")
    transaction_id = fields.Integer()
    # end_transaction_id = fields.Integer()


class MediaItemSchemaListSchema(PaginatedSchema):
    items = fields.Nested("MediaItemSchema", many=True)


def generate_filepath(item, filename):
    if item.event_id:
        return os.path.join(
            current_app.config["UPLOADS_URL"]
            + "event/"
            + str(item.event_id)
            + "/"
            + str(filename)
        )
    elif item.artist_id:
        return os.path.join(
            current_app.config["UPLOADS_URL"]
            + "artist/"
            + str(item.artist_id)
            + "/"
            + str(filename)
        )
    elif item.is_user_avatar:
        return os.path.join(
            current_app.config["UPLOADS_URL"]
            + "user_avatar/"
            + str(item.is_user_avatar.username) +
            '_' + str(item.is_user_avatar.id)
            + "/"
            + str(filename)
        )

def generate_local_filepath(item, filename):
    if item.event_id:
        return os.path.join(
            current_app.config["MEDIA_UPLOAD_FOLDER"]
            + "event/"
            + str(item.event_id)
            + "/"
            + str(filename)
        )
    elif item.artist_id:
        return os.path.join(
            current_app.config["MEDIA_UPLOAD_FOLDER"]
            + "artist/"
            + str(item.artist_id)
            + "/"
            + str(filename)
        )
    elif item.is_user_avatar:
        return os.path.join(
            current_app.config["MEDIA_UPLOAD_FOLDER"]
            + "user_avatar/"
            + str(item.is_user_avatar.username) +
            '_' + str(item.is_user_avatar.id)
            + "/"
            + str(filename)
        )
