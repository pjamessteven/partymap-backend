import pytest
import datetime
from sqlalchemy import and_

from pmapi.user.model import User
from pmapi.notification.model import EmailAction
import pmapi.user.controllers as users
import pmapi.event_tag.controllers as event_tags
from pmapi.extensions import mail


from pmapi.exceptions import InvalidAPIRequest
from pmapi.exceptions import InvalidPermissions
from pmapi.exceptions import RecordAlreadyExists
from pmapi.exceptions import RecordNotFound


def test_get_tags(event_factory):
    # create an event
    event = event_factory("test event")
    tags = ["test1", "test2", "test3"]
    # add tags to event
    event_tags.add_tags_to_event(tags, event)
    # creator will be none when using cli methods. im tired
    all_tags = event_tags.get_tags()
    assert all_tags.total == len(tags)


def test_add_duplicate_tag(event_factory):
    # create an event
    event = event_factory("test event")
    tags = ["test1", "test2", "test3"]
    # add tags to event
    event_tags.add_tags_to_event(tags, event)

    with pytest.raises(RecordAlreadyExists):
        event_tags.add_tags_to_event(tags, event)
