import pytest
from flask import url_for


# ---------------------------------------------------------------------------
# Activity feed endpoints
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="TODO")
def test_get_all_activities(anon_user, complete_event_factory):
    """GET /activity should return all activities grouped by transaction."""
    pass


@pytest.mark.skip(reason="TODO")
def test_get_activities_filtered_by_username(anon_user, complete_event_factory, regular_user):
    """GET /activity?username=... should filter activities to that user."""
    pass


@pytest.mark.skip(reason="TODO")
def test_get_activities_paginated(anon_user, complete_event_factory):
    """GET /activity?page=... should paginate activities."""
    pass


@pytest.mark.skip(reason="TODO")
def test_get_activities_of_transaction(anon_user, complete_event_factory):
    """GET /activity/transaction/<transaction_id>/ should return activities for a transaction."""
    pass
