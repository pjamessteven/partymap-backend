from marshmallow import Schema, fields, validate

class UrlRankingSchema(Schema):
    """
    Marshmallow schema for individual URL ranking data in the summary.
    """
    url = fields.Str(required=True, description="The URL path that was tracked.")
    views = fields.Int(required=True, description="The total number of page views for this URL.")
    unique_views = fields.Int(required=True, description="The number of unique visitors for this URL.")
    avg_speed = fields.Float(allow_none=True, description="The average speed (in seconds) for requests to this URL.")
    error_count = fields.Int(required=True, description="The number of requests to this URL that resulted in an error (status >= 400).")
    error_rate = fields.Float(required=True, description="The percentage of requests to this URL that resulted in an error.")
    type = fields.Str(allow_none=True, description="The type of entity if the URL corresponds to an API endpoint (e.g., 'event', 'artist').")
    name = fields.Str(allow_none=True, description="The name of the associated event or artist, if applicable.")
    display_url = fields.Str(allow_none=True, description="A user-friendly URL for displaying the associated event or artist in the UI.")

class UrlSummarySortableSchema(Schema):
    """
    Marshmallow schema for the overall URL summary response from get_url_summary_sortable.
    """
    total_page_views = fields.Int(required=True, description="The total number of page views across all tracked URLs in the period.")
    total_unique_visitors = fields.Int(required=True, description="The total number of unique visitors across all tracked URLs in the period.")
    url_rankings = fields.List(
        fields.Nested(UrlRankingSchema),
        required=True,
        description="A list of ranked URLs, including detailed metrics and entity-specific information."
    )
    start_time = fields.DateTime(required=True, description="The start of the time period for the summary (ISO 8601 format).")
    end_time = fields.DateTime(required=True, description="The end of the time period for the summary (ISO 8601 format).")


class CountryRankingSchema(Schema):
    """
    Marshmallow schema for individual country ranking data.
    """
    country = fields.Str(required=True, description="The name of the country.")
    unique_visitors = fields.Int(required=True, description="The number of unique visitors from this country.")
    page_views = fields.Int(required=True, description="The total number of page views from this country.")

class CountryVisitorSummarySchema(Schema):
    """
    Marshmallow schema for the overall country visitor summary response.
    """
    total_page_views = fields.Int(required=True, description="The total number of page views across all countries in the period.")
    total_unique_visitors = fields.Int(required=True, description="The total number of unique visitors across all countries in the period.")
    country_rankings = fields.List(
        fields.Nested(CountryRankingSchema),
        required=True,
        description="A list of country rankings, including unique visitors and page views."
    )
    start_time = fields.DateTime(required=True, description="The start of the time period for the summary (ISO 8601 format).")
    end_time = fields.DateTime(required=True, description="The end of the time period for the summary (ISO 8601 format).")
