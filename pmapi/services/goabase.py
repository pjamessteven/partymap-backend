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
                item['url'] for item in event_list.get('itemListElement', [])
                if 'url' in item
            ]
            
            self.logger.info(f"Fetched {len(event_urls)} event URLs")
            return event_urls
        
        except requests.RequestException as e:
            self.logger.error(f"Error fetching event list: {e}")
            return []

    def _extract_hashtags(text):
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

            response = requests.get(event_url.replace('jsonld', 'json'))
            responseld = requests.get(event_url)
            response.raise_for_status()
            responseld.raise_for_status()

            json = response.json().get('party', {})
            json_ld = responseld.json()
            lineup = json_ld.get('performers')
            full_description = self._parse_description(json_ld.get('description'), lineup)
            print('DEWSC', full_description)
            name_type = json_ld.get('nameType', None)
            tags = ['goabase', 'psy']

            if name_type is not None:
                tags.append(name_type)

            # try get hashtag style tags from description
            description_tags = self._extract_hashtags(full_description)
            for tag in description_tags:
                tags.append(tag)

            # Transform event data to desired schema
            transformed_event = {
                'name': json_ld.get('name', None),
                'description': self._parse_summary(full_description, lineup),
                'full_description': full_description,
                'date_time': {'start': self._parse_datetime(json_ld.get('startDate')), 'end': self._parse_datetime(json_ld.get('endDate'))},
                'location': self._get_location(json_ld.get('location')),
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
            return {}
        except Exception as e:
            self.logger.error(f"Unexpected error processing event: {e}")
            return {}

    def _parse_summary(self, description: str) -> str:
        if (description and len(description) > 0): 
            # in the case of no description use the lineup
            summary = description[0:297]
            if len(description) > 297:
                summary += '...'
            return summary
        
    def _parse_description(self, description: str, lineup: str) -> str:
        if not description or len(description) == 0 or description == 'coming':
            # in the case of no description use the lineup
            return lineup 
        elif (description and len(description) > 3): 
            description = description
            if description and lineup and len(lineup) > 1:
                description = description + '/n/n' + lineup
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
        
        for url in event_urls:

            event = self.fetch_event_details(url)

            goabase_url = event.get('url', '')
            goabase_modified = event.get('modified', '')
            existing_event = db.session.query(Event).join(Event.event_dates).filter(EventDate.url == goabase_url).first()   

            if existing_event:
                print('Event already in db')
                existing_modified = existing_event.settings.get('goabase_modified', None) if existing_event.settings else None
                if existing_modified:
                    existing_modified_parsed = parser.parse(existing_modified)
                    goabase_modified_parsed = parser.parse(goabase_modified)
                    if existing_modified_parsed < goabase_modified_parsed:
                        print('Updating existing goabase event:')
                        # TODO
                else:
                    print('No updates... skipping.')
                continue
            try: 
                performers = event.get('performers', '')
                lineup_text = performers  + ' ' + event.get('description', '') 
                image_url = event.get('logo', {}).get('url', '')
                event = events.add_event(**event)
                if event.settings is None:
                    event.settings = {}  # Initialize as an empty dict if None
                event.settings = {**event.settings, "goabase_modified": goabase_modified}
                db.session.add(event)
                db.session.commit()
                event_id = event.id
                if lineup_text and len(lineup_text) > 0 and performers != 'tba':
                    from pmapi.celery_tasks import get_lineup_from_image_and_text
                    get_lineup_from_image_and_text.delay(event_id, lineup_text, image_url)
            except Exception as e:
                print('failed to add event:')
                print(event) 
                print(e)
                traceback.print_exc()  # Prints the detailed stack trace to the console

            if event:
                added_events.append(event)
        
        self.logger.info(f"Successfully processed {len(added_events)} events")
        return added_events

def fetch_events_from_goabase():
    fetcher = GoabaseEventFetcher()
    all_events = fetcher.get_all_events()
    
    # Pretty print first event for demonstration
    import json
    if all_events:
        print(json.dumps(all_events[0], indent=2))