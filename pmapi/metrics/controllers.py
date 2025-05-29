from collections import Counter
from datetime import datetime
import json
import os
import re
from pmapi.event.model import Event
from pmapi.event_artist.model import Artist
from pmapi.extensions import db
from typing import Dict, Any, List, Optional
from pmapi.metrics.model import FlaskUsage
from sqlalchemy import desc as _desc, asc as _asc, func, distinct, case
from sqlalchemy.dialects import postgresql # Import for JSONB-specific functions

def get_url_summary_sortable(
    start_time: datetime,
    end_time: datetime,
    limit: int = 200,
    sort: str = 'views',
    desc: bool = True,
    country: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Summarizes page views within a given time period and ranks URLs by popularity,
    including unique views, average speed, and error rate, with sorting options.
    Filters by country (if provided) for detailed rankings, but overall counts
    include all traffic. Response URLs are filtered to /api/event and /api/artist
    and enriched with event/artist names and display URLs.

    Optimized for PostgreSQL JSONB for country filtering.

    Args:
        db: Your SQLAlchemy database instance (e.g., db from Flask-SQLAlchemy).
        start_time (datetime): The start of the time period (inclusive).
        end_time (datetime): The end of the time period (inclusive).
        limit (int, optional): The maximum number of top URLs to return.
                               If None, all unique URLs within the period are returned.
        sort (str, optional): The metric to sort by. Valid options:
                                 'views', 'unique_views', 'avg_speed', 'error_rate', 'url'.
                                 Defaults to 'views'.
        desc (bool, optional): The sorting order. True for descending, False for ascending.
        country (str, optional): An ISO country code (e.g., 'US', 'NZ') to filter
                                 the detailed URL rankings by. Overall counts are not filtered.

    Returns:
        dict: A dictionary containing:
            'total_page_views': The total number of page views in the period (unfiltered by country).
            'total_unique_visitors': The total number of unique users (unfiltered by country).
            'url_rankings': A list of dictionaries, each with 'url', 'views', 'unique_views',
                            'avg_speed', 'error_count', 'error_rate', 'type', 'name', 'display_url',
                            ranked according to 'sort' and 'desc'.
                            Only includes URLs starting with /api/event or /api/artist.
            'start_time': The provided start time.
            'end_time': The provided end time.
        Returns an empty dictionary if no data is found for the given period.
    """
    if not isinstance(start_time, datetime) or not isinstance(end_time, datetime):
        raise TypeError("start_time and end_time must be datetime objects.")
    if start_time >= end_time:
        raise ValueError("start_time must be before end_time.")

    valid_sort = ['views', 'unique_views', 'avg_speed', 'error_rate', 'url']
    if sort not in valid_sort:
        raise ValueError(f"Invalid sort parameter. Must be one of: {', '.join(valid_sort)}")

    WEBSITE_URL = os.getenv("WEBSITE_URL", "http://localhost:9000")

    try:
        # --- Calculate overall counts (total_page_views, total_unique_visitors) ---
        overall_base_query = db.session.query(FlaskUsage).filter(
            FlaskUsage.datetime >= start_time,
            FlaskUsage.datetime <= end_time
        )

        total_page_views_overall = overall_base_query.with_entities(
            func.count(FlaskUsage.id)
        ).scalar()
        if total_page_views_overall is None:
            total_page_views_overall = 0

        total_unique_visitors_overall = overall_base_query.with_entities(
            func.count(distinct(FlaskUsage.remote_addr))
        ).scalar()
        if total_unique_visitors_overall is None:
            total_unique_visitors_overall = 0

        # --- Build query for URL-specific metrics with DB-side filtering ---
        # Only select relevant columns for the aggregation
        url_metrics_query = db.session.query(
            FlaskUsage.url,
            func.count(FlaskUsage.id).label('views'),
            func.count(distinct(FlaskUsage.remote_addr)).label('unique_views'),
            func.avg(FlaskUsage.speed).label('avg_speed'),
            func.sum(case((FlaskUsage.status >= 400, 1), else_=0)).label('error_count')
        ).filter(
            FlaskUsage.datetime >= start_time,
            FlaskUsage.datetime <= end_time,
            FlaskUsage.remote_addr.isnot(None) # Ensure remote_addr exists
        )

        # Apply country filtering directly in the database query using JSONB operators
        if country:
            # Requires FlaskUsage.ip_info to be JSONB type in PostgreSQL
            url_metrics_query = url_metrics_query.filter(
                func.jsonb_extract_path_text(FlaskUsage.ip_info, 'country') == country
            )

        url_metrics_query = url_metrics_query.filter(
            # Matches /api/event/ followed by at least one character, then anything.
            # This prevents /api/event/ and /api/event? (if no slash) from matching.
            # It will still match /api/event/abc or /api/event/?
            (FlaskUsage.url.like('%/api/event/_%')) |

            # For artist: Match if it has something after /artist/,
            # AND it does NOT contain /api/artist/? immediately after the /artist/ segment.
            # This WILL still incorrectly exclude /api/artist/123?param=value
            # because it contains '/api/artist/?'.
            (FlaskUsage.url.like('%/api/artist/_%') & ~FlaskUsage.url.like('%/api/artist/?%'))
        )



        url_metrics_query = url_metrics_query.group_by(FlaskUsage.url)

        # Apply sorting
        order_func = _desc if desc else _asc

        if sort == 'views':
            url_metrics_query = url_metrics_query.order_by(order_func('views'))
        elif sort == 'unique_views':
            url_metrics_query = url_metrics_query.order_by(order_func('unique_views'))
        elif sort == 'avg_speed':
            url_metrics_query = url_metrics_query.order_by(order_func('avg_speed'))
        elif sort == 'error_rate':
            error_rate_expression = (
                (func.sum(case((FlaskUsage.status >= 400, 1), else_=0)) * 100.0) /
                func.nullif(func.count(FlaskUsage.id), 0)
            )
            # Add this expression to the select list for sorting
            url_metrics_query = url_metrics_query.add_columns(error_rate_expression.label('calculated_error_rate'))
            url_metrics_query = url_metrics_query.order_by(order_func('calculated_error_rate'))
        elif sort == 'url':
            url_metrics_query = url_metrics_query.order_by(order_func(FlaskUsage.url))

        # Apply limit after sorting
        # if limit is not None and limit > 0:
           #  url_metrics_query = url_metrics_query.limit(limit)

        url_data = url_metrics_query.all() # Execute the query
        print(url_data, 'daa')
        # --- Post-processing for enrichment (Event/Artist names and display URLs) ---
        url_rankings = []
        event_ids_to_fetch = set()
        artist_ids_to_fetch = set()


        event_url_pattern = re.compile(r'/event/(\d+)\b')
        artist_url_pattern = re.compile(r'/artist/(\d+)\b')
        # First pass to extract IDs for batch fetching
        for item in url_data:
            url = item.url
            print('url', url)
            match_event = event_url_pattern.search(url)
            match_artist = artist_url_pattern.search(url)

            print(match_event, 'match')
            if match_event:
                event_ids_to_fetch.add(int(match_event.group(1)))
            elif match_artist:
                artist_ids_to_fetch.add(int(match_artist.group(1)))

        # Fetch Event and Artist names in batches
        event_names_map = {}
        if event_ids_to_fetch:
            # Ensure 'Event' model is globally accessible or passed in
            try:
                events = db.session.query(Event).filter(Event.id.in_(list(event_ids_to_fetch))).all()
                event_names_map = {event.id: event.name for event in events}
            except NameError:
                print("Warning: Event model not found. Cannot enrich event names.")
        print(event_names_map, event_ids_to_fetch)
        artist_names_map = {}
        if artist_ids_to_fetch:
            # Ensure 'Artist' model is globally accessible or passed in
            try:
                artists = db.session.query(Artist).filter(Artist.id.in_(list(artist_ids_to_fetch))).all()
                artist_names_map = {artist.id: artist.name for artist in artists}
            except NameError:
                print("Warning: Artist model not found. Cannot enrich artist names.")

        # Second pass to build final url_rankings with enrichment
        for item in url_data:
            url = item.url
            item_type = None
            item_id = None
            item_name = None
            display_url = None

            match_event = event_url_pattern.search(url)
            match_artist = artist_url_pattern.search(url)

            if match_event:
                item_type = 'event'
                item_id = int(match_event.group(1))
                item_name = event_names_map.get(item_id)
                if item_name:
                    encoded_name = re.sub(r'\s+', '_', item_name)
                    display_url = f"{WEBSITE_URL}/event/{item_id}?name={encoded_name}"
            elif match_artist:
                item_type = 'artist'
                item_id = int(match_artist.group(1))
                item_name = artist_names_map.get(item_id)
                if item_name:
                    encoded_name = re.sub(r'\s+', '_', item_name)
                    display_url = f"{WEBSITE_URL}/artist/{item_id}?name={encoded_name}"

            # Calculate error rate if not already calculated for sorting
            error_rate_val = getattr(item, 'calculated_error_rate', None)
            if error_rate_val is None:
                error_rate_val = (item.error_count / item.views * 100) if item.views > 0 else 0


            url_rankings.append({
                'url': item.url,
                'views': item.views,
                'unique_views': item.unique_views,
                'avg_speed': round(item.avg_speed, 2) if item.avg_speed is not None else None,
                'error_count': item.error_count,
                'error_rate': round(error_rate_val, 2),
                'type': item_type,
                'name': item_name,
                'display_url': display_url
            })

        return {
            'total_page_views': total_page_views_overall,
            'total_unique_visitors': total_unique_visitors_overall,
            'url_rankings': url_rankings,
            'start_time': start_time,
            'end_time': end_time
        }

    except Exception as e:
        print(f"An error occurred while getting sortable page view summary: {e}")
        return {}

def get_country_visitor_summary(
    start_time: datetime,
    end_time: datetime,
    limit: int = None,
    desc: bool = True,
    **kwargs
) -> Dict[str, Any]:
    """
    Summarizes unique visitors and page views by country within a given time period,
    based on the 'country' field in the ip_info JSONB, and unique remote_addr,
    and ranks them by popularity (unique visitors by default).

    Args:
        db: Your SQLAlchemy database instance.
        start_time (datetime): The start of the time period (inclusive).
        end_time (datetime): The end of the time period (inclusive).
        limit (int, optional): The maximum number of top countries to return.
                               If None, all unique countries within the period are returned.
        desc (bool, optional): The sorting order. True for descending, False for ascending.
                               Defaults to True.

    Returns:
        dict: A dictionary containing:
            'total_page_views': The total number of page views in the period.
            'total_unique_visitors': The total number of unique visitors in the period.
            'country_rankings': A list of dictionaries, each with 'country', 'country_code',
                                'page_views', and 'unique_visitors',
                                ranked by unique visitors (descending by default).
            'start_time': The provided start time.
            'end_time': The provided end time.
        Returns an empty dictionary if no data is found or ip_info parsing fails for all records.
    """
    if not isinstance(start_time, datetime) or not isinstance(end_time, datetime):
        raise TypeError("start_time and end_time must be datetime objects.")
    if start_time >= end_time:
        raise ValueError("start_time must be before end_time.")

    try:
        # Step 1: Fetch relevant data from the database within the time range
        # Select datetime, ip_info, and remote_addr
        records = db.session.query(
            FlaskUsage.remote_addr,
            FlaskUsage.ip_info
        ).filter(
            FlaskUsage.datetime >= start_time,
            FlaskUsage.datetime <= end_time,
            FlaskUsage.ip_info.isnot(None), # Only include records where ip_info exists
            FlaskUsage.remote_addr.isnot(None) # Only include records where remote_addr exists
        ).all()

        if not records:
            return {
                'total_page_views': 0,
                'total_unique_visitors': 0,
                'country_rankings': [],
                'start_time': start_time,
                'end_time': end_time
            }

        # Dictionary to store unique remote_addr for each country
        country_unique_visitors: Dict[str, set] = {}
        # Counter for page views per country
        country_page_views: Counter = Counter()

        # Step 2: Process ip_info (now a dict) and track unique remote_addr and page views in Python
        # ip_info will now be a Python dict directly from SQLAlchemy's JSONB handling
        for remote_addr, ip_info in records:

            print('ip_info', ip_info['country'])
            try:
                country = ip_info.get('country')

                if country:
                    # Track unique visitors
                    if country not in country_unique_visitors:
                        country_unique_visitors[country] = set()
                    country_unique_visitors[country].add(remote_addr)

                    # Track page views
                    country_page_views[country] += 1

            except (AttributeError, TypeError) as e:
                # Catch AttributeError/TypeError if ip_info isn't a dict or if .get() fails unexpectedly
                print(f"Warning: Could not process ip_info for remote_addr {remote_addr}: {ip_info} - Error: {e}")
                continue # Skip to the next record

        # Step 3: Calculate the number of unique visitors and page views per country and totals
        total_unique_visitors_overall = 0
        total_page_views_overall = 0
        country_rankings_list: List[Dict[str, Any]] = []

        # Iterate over all countries found in either unique visitors or page views
        all_countries = set(country_unique_visitors.keys()).union(set(country_page_views.keys()))

        for country in all_countries:
            num_unique_visitors = len(country_unique_visitors.get(country, set()))
            num_page_views = country_page_views.get(country, 0)

            total_unique_visitors_overall += num_unique_visitors
            total_page_views_overall += num_page_views

            country_rankings_list.append({
                'country': country,
                'unique_visitors': num_unique_visitors,
                'page_views': num_page_views
            })

        # Sort the list (defaulting to unique_visitors for ranking)
        if desc:
            country_rankings_list.sort(key=lambda x: x['unique_visitors'], reverse=True)
        else:
            country_rankings_list.sort(key=lambda x: x['unique_visitors'])

        # Apply limit if specified
        if limit is not None and limit > 0:
            country_rankings_list = country_rankings_list[:limit]

        return {
            'total_page_views': total_page_views_overall,
            'total_unique_visitors': total_unique_visitors_overall,
            'country_rankings': country_rankings_list,
            'start_time': start_time,
            'end_time': end_time
        }

    except Exception as e:
        print(f"An error occurred while getting country summary: {e}")
        return {}
