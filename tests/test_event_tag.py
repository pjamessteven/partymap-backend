from flask import url_for
import pmapi.event_tag.controllers as tag_controllers
from pmapi.event_tag.model import Tag, EventTag
from pmapi.extensions import db


def test_get_event_tags_basic(regular_user, complete_event_factory):
    """GET /tags/ should return tags associated with events."""
    event = complete_event_factory(creator=regular_user, tags=["psychedelic", "techno"])

    rv = regular_user.client.get(url_for("tags.TagsResource"))
    assert rv.status_code == 200
    tags = [t["tag"] for t in rv.json["items"]]
    assert "psychedelic" in tags
    assert "techno" in tags


def test_get_event_tags_by_name(regular_user, complete_event_factory):
    """GET /tags/?tag_name=... should filter tags via full-text search."""
    complete_event_factory(creator=regular_user, tags=["forest"])
    complete_event_factory(creator=regular_user, tags=["techno"])

    rv = regular_user.client.get(url_for("tags.TagsResource", tag_name="fore"))
    assert rv.status_code == 200
    tags = [t["tag"] for t in rv.json["items"]]
    assert "forest" in tags
    assert "techno" not in tags


def test_update_tag_translations_as_staff(staff_user, regular_user, complete_event_factory):
    """PUT /tags/<tag_name>/translations as staff should update translations."""
    event = complete_event_factory(creator=regular_user, tags=["psytrance"])

    rv = staff_user.client.put(
        url_for("tags.TagTranslationResource", tag_name="psytrance"),
        json={"es": "Psytrance", "de": "Psytrance"},
    )
    assert rv.status_code == 200
    assert rv.json["message"] == "Translations updated"
    assert rv.json["translations"]["es"] == "Psytrance"


def test_update_tag_translations_as_regular_user(regular_user, complete_event_factory):
    """PUT /tags/<tag_name>/translations as regular user should return 403."""
    event = complete_event_factory(creator=regular_user, tags=["psytrance"])

    rv = regular_user.client.put(
        url_for("tags.TagTranslationResource", tag_name="psytrance"),
        json={"es": "Psytrance"},
    )
    assert rv.status_code == 403


def test_delete_tag_as_staff(staff_user, regular_user, complete_event_factory):
    """DELETE /tags/<tag_name>/ as staff should delete the tag."""
    event = complete_event_factory(creator=regular_user, tags=["todelete"])

    rv = staff_user.client.delete(url_for("tags.TagResource", tag_name="todelete"))
    assert rv.status_code == 200
    assert rv.json["message"] == "Tag deleted"

    # Verify tag is gone
    assert db.session.query(Tag).filter(Tag.tag == "todelete").first() is None


def test_delete_tag_as_regular_user(regular_user, complete_event_factory):
    """DELETE /tags/<tag_name>/ as regular user should return 403."""
    event = complete_event_factory(creator=regular_user, tags=["todelete"])

    rv = regular_user.client.delete(url_for("tags.TagResource", tag_name="todelete"))
    assert rv.status_code == 403


def test_delete_tag_not_found_as_staff(staff_user):
    """DELETE /tags/<tag_name>/ for nonexistent tag should return 400."""
    rv = staff_user.client.delete(url_for("tags.TagResource", tag_name="nonexistent"))
    assert rv.status_code == 400


def test_update_tag_translations_invalid_input(staff_user, regular_user, complete_event_factory):
    """PUT /tags/<tag_name>/translations with invalid input should return 400."""
    event = complete_event_factory(creator=regular_user, tags=["psytrance"])

    rv = staff_user.client.put(
        url_for("tags.TagTranslationResource", tag_name="psytrance"),
        json="not a dict",
    )
    assert rv.status_code == 400


def test_get_event_tags_paginated(regular_user, complete_event_factory):
    """GET /tags/ should support pagination."""
    complete_event_factory(creator=regular_user, tags=["tag1"])
    complete_event_factory(creator=regular_user, tags=["tag2"])

    rv = regular_user.client.get(url_for("tags.TagsResource", per_page=1))
    assert rv.status_code == 200
    assert len(rv.json["items"]) == 1
    assert rv.json["total"] >= 2


def test_controller_update_tag_translations(regular_user, complete_event_factory):
    """Controller update_tag_translations should update tag translations."""
    event = complete_event_factory(creator=regular_user, tags=["goa"])
    tag = db.session.query(Tag).filter(Tag.tag == "goa").one()

    updated = tag_controllers.update_tag_translations("goa", {"fr": "Goa", "it": "Goa"})
    assert updated.tag_translations["fr"] == "Goa"
    assert updated.tag_translations["it"] == "Goa"


def test_controller_delete_tag(regular_user, complete_event_factory):
    """Controller delete_tag should delete tag and its event associations."""
    event = complete_event_factory(creator=regular_user, tags=["forest"])

    result = tag_controllers.delete_tag("forest")
    assert result is True
    assert db.session.query(Tag).filter(Tag.tag == "forest").first() is None
    assert db.session.query(EventTag).filter(EventTag.tag_id == "forest").count() == 0


def test_controller_delete_tag_not_found():
    """Controller delete_tag for nonexistent tag should raise InvalidAPIRequest."""
    from pmapi.exceptions import InvalidAPIRequest
    with pytest.raises(InvalidAPIRequest):
        tag_controllers.delete_tag("nonexistent")


def test_controller_update_tag_translations_not_found():
    """Controller update_tag_translations for nonexistent tag should raise InvalidAPIRequest."""
    from pmapi.exceptions import InvalidAPIRequest
    with pytest.raises(InvalidAPIRequest):
        tag_controllers.update_tag_translations("nonexistent", {"en": "Test"})


import pytest
