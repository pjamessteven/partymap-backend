from flask import url_for
import pmapi.event_tag.controllers as event_tags


def test_get_tags(event_factory, regular_user, anon_user):
    # create an event
    event = event_factory("test event")
    tags = ["test1", "test2", "test3"]
    # add tags to event
    event_tags.add_tags_to_event(tags, event, regular_user)
    rv = anon_user.client.get(url_for("tags.TagsResource"))
    assert len(rv.json["items"]) == len(tags)


def test_get_tag_search(event_factory, regular_user, anon_user):
    # create an event
    event = event_factory("test event")
    tags = ["test1", "test2", "test3"]
    # add tags to event
    event_tags.add_tags_to_event(tags, event, regular_user)
    rv = anon_user.client.get(url_for("tags.TagsResource", tag_name="test"))
    assert len(rv.json["items"]) == 3


def test_get_tag_exact(event_factory, regular_user, anon_user):
    # create an event
    event = event_factory("test event")
    tags = ["test1", "test2", "test3"]
    # add tags to event
    event_tags.add_tags_to_event(tags, event, regular_user)
    rv = anon_user.client.get(url_for("tags.TagsResource", tag_name="test1"))

    print(rv.json)
    assert len(rv.json["items"]) == 1


def test_get_tag_not_exist(event_factory, regular_user, anon_user):
    # create an event
    event = event_factory("test event")
    tags = ["test1", "test2", "test3"]
    # add tags to event
    event_tags.add_tags_to_event(tags, event, regular_user)
    rv = anon_user.client.get(url_for("tags.TagsResource", tag_name="test12"))
    assert len(rv.json["items"]) == 0
