import re
import traceback
import requests
from datetime import datetime
from dateutil import parser
from typing import List, Dict, Any
import logging
import time
from pmapi.event.model import Event
from pmapi.event_date.model import EventDate
from pmapi.extensions import db
from pmapi.services.gmaps import get_best_location_result
from pmapi.services.lineup import get_lineup_from_image_and_text
from sqlalchemy import and_, not_, or_, func
import html
from flask.helpers import get_debug_flag
from pmapi.config import DevConfig, ProdConfig
DEV_ENVIRON = get_debug_flag()
CONFIG = DevConfig if DEV_ENVIRON else ProdConfig


class GoabaseEventFetcher:
    def __init__(self, base_url: str = "https://www.goabase.net/api/party/"):
        """
        Initialize the Goabase Event Fetcher
        
        :param base_url: Base URL for Goabase API
        """
        self.base_url = base_url
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)

    def fetch_event_list(self) -> List[str]:
        """
        Fetch the list of event URLs from Goabase
        
        :return: List of event URLs
        """
        try:
            response = requests.get(f"{self.base_url}json/")
            response.raise_for_status()
            event_list = response.json()
            
            # Extract URLs from the list
            event_urls = [
                item['urlPartyJson'] for item in event_list.get('partylist', [])
                if 'urlPartyJson' in item
            ]
            
            self.logger.info(f"Fetched {len(event_urls)} event URLs")
            return event_urls
        
        except requests.RequestException as e:
            self.logger.error(f"Error fetching event list: {e}")
            return []

    def _extract_hashtags(self, text):
        # Use a regular expression to find all words that start with a hashtag (#)
        hashtags = re.findall(r'(?<=#)\w+', text)
        return hashtags

    def fetch_event_details(self, event_url: str) -> Dict[str, Any]:
        """
        Fetch details for a specific event
        
        :param event_url: URL of the event
        :return: Transformed event dictionary
        """
        try:
            # data is served in two formats

            responseld = requests.get(event_url.replace('json', 'jsonld'))
            response = requests.get(event_url)
            response.raise_for_status()
            responseld.raise_for_status()

            json = response.json().get('party', {})
            json_ld = responseld.json()
            lineup = json_ld.get('performers', None)
            full_description = self._parse_description(json_ld.get('description'), lineup)
            name_type = json_ld.get('nameType', None)
            tags = ['goabase']

            if name_type is not None:
                tags.append(name_type)

            # try get hashtag style tags from description
            description_tags = self._extract_hashtags(full_description)
            for tag in description_tags:
                tags.append(tag)

            # Transform event data to desired schema
            transformed_event = {
                'name': json_ld.get('name', None),
                'description': self._parse_summary(full_description),
                'full_description': full_description,
                'date_time': {'start': self._parse_datetime(json_ld.get('startDate')), 'end': self._parse_datetime(json_ld.get('endDate'))},
                'location':json_ld.get('location'),
                'url': json_ld.get('url', ''),
                'performers': json_ld.get('performers', None),
                'tags': tags,
                'modified': json.get('dateModified')
            }
            
            # set logo if exists
            if self._get_event_image(json_ld.get('image', {})) is not None:
                transformed_event = {**transformed_event, "logo": {'url': self._get_event_image(json_ld.get('image', {}))}}

            print('fetched goabase event: ', json_ld.get('name', None))            
            return transformed_event
        
        except requests.RequestException as e:
            self.logger.error(f"Error fetching event details from {event_url}: {e}")
            raise e
        except Exception as e:
            self.logger.error(f"Unexpected error processing event: {e}")
            raise e

    def _parse_summary(self, description: str) -> str:
        if (description and len(description) > 0): 
            # in the case of no description use the lineup
            summary = description[0:297]
            if len(description) > 297:
                summary += '...'
            return summary
        
    def _parse_description(self, description: str, lineup: str) -> str:
        lineup = html.unescape(lineup)
        description = html.unescape(description)
        if not description or len(description) == 0 or description == 'coming':
            # in the case of no description use the lineup
            return lineup
        elif (description and len(description) > 3): 
            if description and lineup and len(lineup) > 1:
                description = description + '\n\n' + lineup
            return description
        else:
            return 'Description coming soon...'

    def _parse_datetime(self, datetime_str: str) -> str:
        """
        Parse and format datetime string
        
        :param datetime_str: ISO 8601 formatted datetime string
        :return: Formatted datetime string
        """
        if not datetime_str:
            return ''
        try:
            dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            return datetime_str

    def _get_location(self, location) -> str:
        parts = []
        address_parts = []
        if name := location.get('name'):
            parts.append(name)

        if address := location.get('address', {}):
            address_parts = [
                address.get('streetAddress', ''),
                address.get('addressLocality', ''),
                address.get('addressCountry', '')
            ]
            parts.append(', '.join(filter(bool, address_parts)))
        
        time.sleep(1)
        location_string = ', '.join(filter(bool, parts))
        print('_get_location getting location: ' + location_string)
        location = get_best_location_result(location_string)
        if not location:
            print('_get_location: trying address instead')
            time.sleep(1)
            location_string = ', '.join(filter(bool, address_parts))
            location = get_best_location_result(location_string)

        if not location:
            print('_get_location: trying name finally')
            time.sleep(1)
            location = get_best_location_result(location.get('name'))
        
        print('_get_location: query: ' + location_string)
        print('_get_location: location result:  ' + location.get('description'))
        return location

    def _get_event_image(self, image: Any) -> str:
        """
        Extract event image URL.
        
        :param image: Image dictionary or array of image dictionaries from event data
        :return: Image URL or empty string
        """
        if isinstance(image, list) and image:  # Check if image is a non-empty list
            image = image[0]  # Pick the first image in the list
        if isinstance(image, dict):  # Ensure it's a dictionary before extracting
            return image.get('url', image.get('thumbnailUrl', None))
        return None  # Return empty string if image is neither a list nor a dictionary

    def get_all_events(self) -> List[Dict[str, Any]]:
        import pmapi.event.controllers as events
        """
        Fetch and transform all events
        
        :return: List of transformed event dictionaries
        """
        event_urls = self.fetch_event_list()
        added_events = []
        total_events = len(event_urls)
        progress_bar_width = 50  # Width of the progress bar in characters

        print("Processing events:")
        for i, url in enumerate(event_urls, 1):
            # Calculate progress percentage
            progress = i / total_events
            filled_length = int(progress_bar_width * progress)
            bar = '█' * filled_length + '-' * (progress_bar_width - filled_length)
            print(f"\r[{bar}] {int(progress * 100)}% ({i}/{total_events})", end="", flush=True)

            # Retry mechanism for fetch_event_details
            max_retries = 3  # Maximum number of retries
            retry_delay = 3  # Delay between retries in seconds
            event = None

            for attempt in range(max_retries):
                try:
                    event = self.fetch_event_details(url)
                    break  # Exit the retry loop if successful
                except Exception as e:
                    print(f"\nAttempt {attempt + 1} failed for URL: {url}")
                    print(f"Error: {e}")
                    if attempt < max_retries - 1:  # Don't wait on the last attempt
                        time.sleep(retry_delay)
                    else:
                        print(f"Max retries reached for URL: {url}. Skipping this event.")
                        continue  # Skip to the next URL if all retries fail

            if not event:
                continue  # Skip to the next URL if event fetching failed
            
            start_str = event.get('date_time', {}).get('start', None) 
            start_time = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
            if start_time < datetime.now():
                print('Ignoring past event. Start time: ' + start_str)
                # ignore past events
                continue

            goabase_url = event.get('url', '')
            goabase_modified = event.get('modified', '')
            performers = event.get('performers', '')
            lineup_text = performers  + ' ' + event.get('description', '') 
            image_url = event.get('logo', {}).get('url', '')

            existing_event = db.session.query(Event).join(Event.event_dates).filter(EventDate.url == goabase_url).first()   

            if existing_event:
                print(f"\nEvent already in db: {existing_event.name}  (#{existing_event.id})")
                existing_modified = existing_event.settings.get('goabase_modified', None) if existing_event.settings else None
            
                should_update = False

                if existing_modified is not None:
                    existing_modified_parsed = parser.parse(existing_modified)
                    goabase_modified_parsed = parser.parse(goabase_modified)
                    if existing_modified_parsed < goabase_modified_parsed:
                        should_update = True

                else: 
                    should_update = True
                    print("No modification date found... updating event.")

                if should_update:
                    print(f"Updating existing goabase event: {existing_event.name} (#{existing_event.id})")
                    print(f"existing_modified: {existing_modified}")
                    print(f"remote_modified: {goabase_modified}")
                    event.update({'location': self._get_location(event.get('location'))})
                    if existing_event.settings is None:
                        existing_event.settings = {}  # Initialize as an empty dict if None
                    existing_event.settings = {**existing_event.settings, "goabase_modified": goabase_modified}
                    events.update_event(existing_event.id, **event)
                    if lineup_text and len(lineup_text) > 0 and performers != 'tba':
                        from pmapi.celery_tasks import get_lineup
                        get_lineup.delay(existing_event.id, lineup_text, image_url)
                    print(f"Updated existing goabase event: {existing_event.name} (#{existing_event.id})")
                else:
                    print("No updates since last sync. Skipping.")
                continue

            try: 
                # get location after pre-existing check
                event.update({'location': self._get_location(event.get('location'))})

                event = events.add_event(**event)
                if event.settings is None:
                    event.settings = {}  # Initialize as an empty dict if None
                event.settings = {**event.settings, "goabase_modified": goabase_modified}
                event.hidden = False
                db.session.add(event)
                db.session.commit()
                event_id = event.id
                if lineup_text and len(lineup_text) > 0 and performers != 'tba':
                    from pmapi.celery_tasks import get_lineup
                    get_lineup.delay(event_id, lineup_text, image_url)
                
                print(f"\nSuccessfully added event: {event.name}")
                added_events.append(event)
            except Exception as e:
                print(f"\nFailed to add event: {event.get('name', 'Unnamed Event')}")
                print(f"Error: {e}")
                traceback.print_exc()  # Prints the detailed stack trace to the console

        print(f"\nCompleted processing. Total events added: {len(added_events)}")
        self.logger.info(f"Successfully processed {len(added_events)} events")
        return added_events

def fetch_events_from_goabase():
    fetcher = GoabaseEventFetcher()
    all_events = fetcher.get_all_events()
    
    # Pretty print first event for demonstration
    import json
    if all_events:
        print(
            'first event:'
        )
        print(json.dumps(all_events[0], indent=2))

# this is automatically done when adding goabase events
# this function allows processing them all manually if something went wrong with 
# the automatic process
def update_goabase_lineup():
    event_query = db.session.query(Event).join(Event.event_dates).filter(EventDate.url.ilike('%goabase%'))
    # only update future events
    event_query = event_query.filter(
        or_(
            and_(EventDate.end.is_(None), EventDate.start > func.now()),  # Event.end is NULL and Event.start > NOW()
            EventDate.end > func.now()  # Event.end is in the future
        )
    )
    event_query = event_query.group_by(Event.id)

    for event in event_query:
        next_date = event.next_event()
        if next_date:
            if next_date.artists is None or (isinstance(next_date.artists, (list)) and len(next_date.artists) == 0):       
                print('processing lineup for: ' + event.name)
                cover_image_url = event.cover_image.url if event.cover_image else None
                print('event.cover_image.url', cover_image_url)
                get_lineup_from_image_and_text(event.id, event.full_description, cover_image_url)
            else:
                print('lineup already exists:.')