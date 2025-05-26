from collections import Counter
from datetime import datetime
import json
from pmapi.extensions import db

from pmapi.metrics.model import FlaskUsage
from sqlalchemy import desc as _desc, asc as _asc, func, distinct, case


def get_url_summary_sortable(
    start_time: datetime,
    end_time: datetime,
    limit: int = 200,
    sort_by: str = 'views',
    desc: bool = True,
    **kwargs
) -> dict:
    """
    Summarizes page views within a given time period and ranks URLs by popularity,
    including unique views, average speed, and error rate, with sorting options.

    Args:
        start_time (datetime): The start of the time period (inclusive).
        end_time (datetime): The end of the time period (inclusive).
        db: Your SQLAlchemy database instance (e.g., db from Flask-SQLAlchemy).
        limit (int, optional): The maximum number of top URLs to return.
                               If None, all unique URLs within the period are returned.
        sort_by (str, optional): The metric to sort by. Valid options:
                                 'views', 'unique_views', 'avg_speed', 'error_rate', 'url'.
                                 Defaults to 'views'.
        desc (Boolean, optional): The sorting order.

    Returns:
        dict: A dictionary containing:
            'total_page_views': The total number of page views in the period.
            'total_unique_visitors': The total number of unique users (across all pages).
            'url_rankings': A list of dictionaries, each with 'url', 'views', 'unique_views',
                            'avg_speed', 'error_count', 'error_rate',
                            ranked according to 'sort_by' and 'sort_order'.
            'start_time': The provided start time.
            'end_time': The provided end time.
        Returns an empty dictionary if no data is found for the given period.
    """
    if not isinstance(start_time, datetime) or not isinstance(end_time, datetime):
        raise TypeError("start_time and end_time must be datetime objects.")
    if start_time >= end_time:
        raise ValueError("start_time must be before end_time.")

    valid_sort_by = ['views', 'unique_views', 'avg_speed', 'error_rate', 'url']
    if sort_by not in valid_sort_by:
        raise ValueError(f"Invalid sort_by parameter. Must be one of: {', '.join(valid_sort_by)}")


    try:
        # Base query filtered by time
        base_query_filtered = db.session.query(FlaskUsage).filter(
            FlaskUsage.datetime >= start_time,
            FlaskUsage.datetime <= end_time
        )

        # Calculate total unique visitors for the period (across all pages)
        # Using 'remote_addr' for unique user identification. Adjust to 'track_var' if that's your unique ID.
        total_unique_visitors = base_query_filtered.with_entities(
            func.count(distinct(FlaskUsage.remote_addr))
        ).scalar()
        if total_unique_visitors is None:
            total_unique_visitors = 0

        # Subquery or Common Table Expression (CTE) to calculate error_count and total views per URL
        # This is often more efficient for complex aggregations and then joining/ordering
        # However, for simplicity here, we'll keep it in one main query with conditional summing.

        # Query for URL-specific metrics
        # We need to explicitly select FlaskUsage.url to group by it
        # func.case is used to count errors based on status code
        url_metrics_query = db.session.query(
            FlaskUsage.url,
            func.count(FlaskUsage.id).label('views'),
            func.count(distinct(FlaskUsage.remote_addr)).label('unique_views'),
            func.avg(FlaskUsage.speed).label('avg_speed'),
            func.sum(case((FlaskUsage.status >= 400, 1), else_=0)).label('error_count')
        ).filter(
            FlaskUsage.datetime >= start_time,
            FlaskUsage.datetime <= end_time
        ).group_by(
            FlaskUsage.url
        )

        # Apply sorting
        order_func = _desc if desc else _asc

        # Map sort_by string to the corresponding SQLAlchemy expression
        if sort_by == 'views':
            url_metrics_query = url_metrics_query.order_by(order_func('views'))
        elif sort_by == 'unique_views':
            url_metrics_query = url_metrics_query.order_by(order_func('unique_views'))
        elif sort_by == 'avg_speed':
            # When sorting by avg_speed, None values (if no speed recorded) might need specific handling
            # Using -float('inf') or float('inf') for NULLs to push them to the end/beginning
            url_metrics_query = url_metrics_query.order_by(order_func(FlaskUsage.speed)) # Sorting directly by the column for avg
        elif sort_by == 'error_rate':
            # Calculate error_rate in Python after fetching, then sort.
            # Or, for database-side sorting, you'd calculate this in the query too:
            # (func.sum(case((FlaskUsage.status >= 400, 1), else_=0)) * 100.0 / func.count(FlaskUsage.id))
            # However, for simplicity and to avoid division by zero in SQL, we'll calculate error_rate in Python
            # and then sort by it if selected. If we choose to sort by error_rate directly in the DB,
            # we must handle potential division by zero (e.g., coalesce(total_views, 1) to avoid divide by zero).
            # For now, we'll assume we can post-sort by this, or we'll add it as a calculated column.
            # To sort directly in the query, we can add it to the select and order_by.
            # Let's add it to the select statement for robust DB-side sorting.
            error_rate_expression = (
                (func.sum(case((FlaskUsage.status >= 400, 1), else_=0)) * 100.0) /
                func.nullif(func.count(FlaskUsage.id), 0) # Use nullif to prevent division by zero
            )
            url_metrics_query = url_metrics_query.add_columns(error_rate_expression.label('calculated_error_rate'))
            url_metrics_query = url_metrics_query.order_by(order_func('calculated_error_rate'))
        elif sort_by == 'url':
            url_metrics_query = url_metrics_query.order_by(order_func(FlaskUsage.url))


        if limit is not None and limit > 0:
            url_metrics_query = url_metrics_query.limit(limit)

        url_data = url_metrics_query.all()

        total_page_views = sum(item.views for item in url_data) if url_data else 0

        url_rankings = []
        for item in url_data:
            # Use 'calculated_error_rate' if it was added to the query for sorting, otherwise calculate it.
            # If sorting by 'error_rate', 'item.calculated_error_rate' will exist.
            # Otherwise, calculate it manually for consistency.
            if hasattr(item, 'calculated_error_rate'):
                error_rate = item.calculated_error_rate
            else:
                error_rate = (item.error_count / item.views * 100) if item.views > 0 else 0

            url_rankings.append({
                'url': item.url,
                'views': item.views,
                'unique_views': item.unique_views,
                'avg_speed': round(item.avg_speed, 2) if item.avg_speed is not None else None,
                'error_count': item.error_count,
                'error_rate': round(error_rate, 2)
            })

        return {
            'total_page_views': total_page_views,
            'total_unique_visitors': total_unique_visitors,
            'url_rankings': url_rankings,
            'start_time': start_time,
            'end_time': end_time
        }

    except Exception as e:
        print(f"An error occurred while getting sortable page view summary: {e}")
        return {}
    except Exception as e:
        # Log the error for debugging
        print(f"An error occurred while getting page view summary: {e}")
        # Optionally re-raise or return a specific error structure
        return {}
    

def get_country_page_view_summary(
    start_time: datetime,
    end_time: datetime,
    limit: int = None,
    desc: bool = True,
    **kwargs
) -> dict:
    """
    Summarizes page views by country within a given time period,
    based on the 'country' field in the ip_info JSON, and ranks them by popularity.

    Args:
        start_time (datetime): The start of the time period (inclusive).
        end_time (datetime): The end of the time period (inclusive).
        db: Your SQLAlchemy database instance.
        limit (int, optional): The maximum number of top countries to return.
                               If None, all unique countries within the period are returned.
        sort_order (str, optional): The sorting order. 'asc' for ascending, 'desc' for descending.
                                    Defaults to 'desc'.

    Returns:
        dict: A dictionary containing:
            'total_page_views': The total number of page views in the period.
            'country_rankings': A list of dictionaries, each with 'country', 'country_code', 'views',
                                ranked by views in descending order.
            'start_time': The provided start time.
            'end_time': The provided end time.
        Returns an empty dictionary if no data is found or ip_info parsing fails for all records.
    """
    if not isinstance(start_time, datetime) or not isinstance(end_time, datetime):
        raise TypeError("start_time and end_time must be datetime objects.")
    if start_time >= end_time:
        raise ValueError("start_time must be before end_time.")

    # We cannot directly query JSON fields in a portable way with SQLAlchemy's `func`
    # unless using database-specific functions (e.g., PostgreSQL's jsonb_extract_path_text).
    # For cross-database compatibility (like SQLite for testing), we'll fetch a subset
    # and then process in Python.
    # For production with PostgreSQL, consider using jsonb_extract_path_text for efficiency.

    try:
        # Step 1: Fetch relevant data from the database within the time range
        # Select datetime, ip_info, and id (for counting)
        records = db.session.query(
            FlaskUsage.id,
            FlaskUsage.ip_info
        ).filter(
            FlaskUsage.datetime >= start_time,
            FlaskUsage.datetime <= end_time,
            FlaskUsage.ip_info.isnot(None) # Only include records where ip_info exists
        ).all()

        if not records:
            return {
                'total_page_views': 0,
                'country_rankings': [],
                'start_time': start_time,
                'end_time': end_time
            }

        country_views = Counter()
        country_codes = {} # To store country code mapping

        # Step 2: Process ip_info JSON in Python
        for record_id, ip_info_json_str in records:
            try:
                ip_data = json.loads(ip_info_json_str)
                country = ip_data.get('country')
                country_code = ip_data.get('countryCode')

                if country:
                    country_views[country] += 1
                    if country_code:
                        country_codes[country] = country_code
            except (json.JSONDecodeError, AttributeError, TypeError) as e:
                # Log or print an error if ip_info is malformed
                print(f"Warning: Could not parse ip_info for record ID {record_id}: {ip_info_json_str} - Error: {e}")
                continue # Skip to the next record

        # Step 3: Format and sort results
        total_page_views = sum(country_views.values())
        country_rankings_list = []

        for country, views in country_views.items():
            country_rankings_list.append({
                'country': country,
                'country_code': country_codes.get(country), # Get the associated country code
                'views': views
            })

        # Sort the list
        if desc:
            country_rankings_list.sort(key=lambda x: x['views'], reverse=True)
        else:
            country_rankings_list.sort(key=lambda x: x['views'])

        # Apply limit if specified
        if limit is not None and limit > 0:
            country_rankings_list = country_rankings_list[:limit]

        return {
            'total_page_views': total_page_views,
            'country_rankings': country_rankings_list,
        }

    except Exception as e:
        print(f"An error occurred while getting country page view summary: {e}")
        return {}