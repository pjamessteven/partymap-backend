import pytest
import pmapi.event_tag.controllers as event_tags

from pmapi.exceptions import RecordAlreadyExists


def test_get_tags(event_factory, regular_user):
    # create an event
    event = event_factory("test event")
    tags = ["test1", "test2", "test3"]
    # add tags to event
    event_tags.add_tags_to_event(tags, event)
    # creator will be none when using cli methods. im tired
    all_tags = event_tags.get_tags()
    print(all_tags.items)
    assert all_tags.total == len(tags)


def test_add_duplicate_tag(event_factory, regular_user):
    # create an event
    event = event_factory("test event")
    tags = ["test1", "test2", "test3"]
    # add tags to event
    event_tags.add_tags_to_event(tags, event)

    with pytest.raises(RecordAlreadyExists):
        event_tags.add_tags_to_event(tags, event)
