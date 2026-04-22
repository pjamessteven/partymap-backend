import pytest
from flask import url_for


# ---------------------------------------------------------------------------
# Metrics endpoints
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="TODO")
def test_get_url_metrics(anon_user):
    """GET /metrics/urls should return URL usage metrics."""
    pass


@pytest.mark.skip(reason="TODO")
def test_get_url_metrics_with_filters(anon_user):
    """GET /metrics/urls?country=...&start_time=... should filter metrics."""
    pass


@pytest.mark.skip(reason="TODO")
def test_get_country_metrics(anon_user):
    """GET /metrics/countries should return country visitor metrics."""
    pass


@pytest.mark.skip(reason="TODO")
def test_get_country_metrics_with_date_range(anon_user):
    """GET /metrics/countries?start_time=...&end_time=... should filter by date."""
    pass
