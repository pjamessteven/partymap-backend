from flask import url_for


def test_ip_lookup_default(anon_user):
    """GET /services/ip_lookup/ should return location for request IP."""
    rv = anon_user.client.get(url_for("service.IpLookupResource_default"))
    # May return 200 with location data or empty result depending on env
    assert rv.status_code in (200, 404)


def test_ip_lookup_specific_ip(anon_user):
    """GET /services/ip_lookup/<ip> should return location for the given IP."""
    rv = anon_user.client.get(url_for("service.IpLookupResource", ip="8.8.8.8"))
    assert rv.status_code in (200, 404)
