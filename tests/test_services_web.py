import pytest
from flask import url_for


# ---------------------------------------------------------------------------
# Services endpoints
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="TODO")
def test_ip_lookup_default(anon_user):
    """GET /services/ip_lookup/ should return location for request IP."""
    pass


@pytest.mark.skip(reason="TODO")
def test_ip_lookup_specific_ip(anon_user):
    """GET /services/ip_lookup/<ip> should return location for the given IP."""
    pass
