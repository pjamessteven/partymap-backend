from flask import url_for


from datetime import datetime, timedelta


def test_get_url_metrics(anon_user):
    """GET /metrics/urls should return URL metrics."""
    end = datetime.utcnow()
    start = end - timedelta(days=7)
    rv = anon_user.client.get(
        url_for("metrics.UrlMetricResource", start_time=start.isoformat(), end_time=end.isoformat())
    )
    assert rv.status_code == 200
    assert "url_rankings" in rv.json


def test_get_country_metrics(anon_user):
    """GET /metrics/countries should return country visitor metrics."""
    end = datetime.utcnow()
    start = end - timedelta(days=7)
    rv = anon_user.client.get(
        url_for("metrics.CountryMetricResource", start_time=start.isoformat(), end_time=end.isoformat())
    )
    assert rv.status_code == 200
    assert "country_rankings" in rv.json


def test_get_url_metrics_with_sort(anon_user):
    """GET /metrics/urls?sort=views should sort by views."""
    end = datetime.utcnow()
    start = end - timedelta(days=7)
    rv = anon_user.client.get(
        url_for("metrics.UrlMetricResource", sort="views", start_time=start.isoformat(), end_time=end.isoformat())
    )
    assert rv.status_code == 200
    assert "url_rankings" in rv.json
