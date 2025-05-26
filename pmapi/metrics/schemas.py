from marshmallow import Schema, fields, validate

class URLRankingSchema(Schema):
    """
    Marshmallow schema for individual URL ranking items.
    """
    url = fields.String(required=True, description="The URL of the page.")
    views = fields.Integer(required=True, description="Total page views for this URL.")
    unique_views = fields.Integer(required=True, description="Number of unique visitors for this URL.")
    avg_speed = fields.Float(allow_none=True, description="Average response time in seconds for this URL.")
    error_count = fields.Integer(required=True, description="Number of error responses (HTTP 4xx or 5xx) for this URL.")
    error_rate = fields.Float(required=True, description="Percentage of error responses for this URL.")

class PageViewSummarySchema(Schema):
    """
    Marshmallow schema for the overall page view summary.
    """
    total_page_views = fields.Integer(required=True, description="Total page views across all URLs in the period.")
    total_unique_visitors = fields.Integer(required=True, description="Total unique visitors across all URLs in the period.")
    url_rankings = fields.List(fields.Nested(URLRankingSchema), required=True, description="Ranked list of URLs by popularity.")
    start_time = fields.DateTime(format='iso', required=True, description="The start time of the queried period (ISO 8601 format).")
    end_time = fields.DateTime(format='iso', required=True, description="The end time of the queried period (ISO 8601 format).")

class CountryRankingSchema(Schema):
    """
    Marshmallow schema for individual country ranking items.
    """
    country = fields.String(required=True, description="The name of the country.")
    views = fields.Integer(required=True, description="Total page views from this country.")

class CountryPageViewSummarySchema(Schema):
    """
    Marshmallow schema for the overall country page view summary.
    """
    total_page_views = fields.Integer(required=True, description="Total page views across all countries in the period.")
    country_rankings = fields.List(fields.Nested(CountryRankingSchema), required=True, description="Ranked list of countries by page views.")
    start_time = fields.DateTime(format='iso', required=True, description="The start time of the queried period (ISO 8601 format).")
    end_time = fields.DateTime(format='iso', required=True, description="The end time of the queried period (ISO 8601 format).")