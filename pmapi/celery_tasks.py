from psycopg2 import OperationalError
import time
import os
from flask.helpers import get_debug_flag
import logging
from pmapi.event.model import Event
from pmapi.event_artist.model import Artist
from pmapi.event_date.model import EventDate
from pmapi.event_review.model import EventReview
from pmapi.extensions import mail
from ffmpy import FFmpeg
from .config import DevConfig
from .config import ProdConfig
from requests.exceptions import RequestException
from pmapi.extensions import db
from pmapi.utils import SUPPORTED_LANGUAGES, get_translation
from flask import g
from typing import List, Dict, Any
import requests

DEV_ENVIRON = get_debug_flag()
CONFIG = DevConfig if DEV_ENVIRON else ProdConfig

from pmapi.worker import celery

@celery.task(ignore_result=True)
def background_send_mail(
    to, subject, content, content_type, from_=None, msg_type="unknown"
):
    result = mail.send(to, subject, content, content_type, from_)
    logging.info(
        "send.mail",
        to=to,
        subject=subject,
        status=result and "sent" or "failed",
        msg_type=msg_type,
    )
    return result


@celery.task()
def run_video_conversion(
    input_filepath,
    output_filepath,
    min_bitrate,
    target_bitrate,
    max_bitrate,
    width,
    height,
):
    ff = FFmpeg(
        executable="/usr/bin/ffmpeg",
        inputs={input_filepath: None},
        outputs={
            output_filepath: "-c:a libvorbis -c:v vp9 -b:v {0}k -minrate {1}k -maxrate {2}k \
             -quality good -speed 4 -c:a libvorbis -vf scale={3}x{4}".format(
                target_bitrate, min_bitrate, max_bitrate, width, height
            )
        },
    )
    ff.run()


@celery.task()
def get_video_thumbnail(
    input_filepath,
    thumb_out_filepath,
    poster_out_filepath,
    thumb_width=None,
    thumb_height=None,
):
    ff = FFmpeg(
        executable="/usr/bin/ffmpeg",
        inputs={input_filepath: None},
        outputs={
            thumb_out_filepath: "-ss 00:00:01.000 -vframes 1 -vf scale={0}x{1}".format(
                thumb_width, thumb_height
            )
        },
    )
    ff.run()
    ff = FFmpeg(
        executable="/usr/bin/ffmpeg",
        inputs={input_filepath: None},
        outputs={poster_out_filepath: "-ss 00:00:01.000 -vframes 1"},
    )
    ff.run()


@celery.task(autoretry_for=(RequestException, OperationalError), retry_backoff=True, retry_backoff_max=120, rate_limit="30/m"
)
def refresh_artist_info(artist_id):
    from pmapi.event_artist.controllers import refresh_info
    refresh_info(artist_id)

@celery.task(autoretry_for=(RequestException, OperationalError), retry_backoff=True, retry_backoff_max=120, rate_limit="30/m"
)
def update_event_translation(event_id):
    event = db.session.query(Event).filter(Event.id == event_id).first()
    event.description_translations = update_translation_field(event.description_translations, event.description)
    event.full_description_translations = update_translation_field(event.full_description_translations, event.full_description)
    db.session.commit()
    db.session.close()

@celery.task(autoretry_for=(RequestException,OperationalError), retry_backoff=True, retry_backoff_max=120, rate_limit="30/m"
)
def update_event_date_translation(id):
    event_date = db.session.query(EventDate).filter(EventDate.id == id).first()
    event_date.description_translations = update_translation_field(event_date.description_translations, event_date.description)
    db.session.commit()

@celery.task(autoretry_for=(RequestException,OperationalError), retry_backoff=True, retry_backoff_max=120, rate_limit="30/m"
)
def update_artist_translation(id):
    artist = db.session.query(Artist).filter(Artist.id == id).first()
    if (artist.disambiguation):
        artist.description_translations = update_translation_field(artist.disambiguation_translations, artist.disambiguation)
    if (artist.description):
        artist.description_translations = update_translation_field(artist.description_translations, artist.description)
    db.session.commit()


@celery.task(autoretry_for=(RequestException,OperationalError), retry_backoff=True, retry_backoff_max=120, rate_limit="30/m"
)
def update_review_translation(id):
    review = db.session.query(EventReview).filter(EventReview.id == id).first()
    review.text_translations = update_translation_field(review.text_translations, review.text)
    db.session.commit()
    

def update_translation_field(translation_field, input_text, onlyMissing=False):
    if translation_field is None:
        translation_field = {}

    for lang in SUPPORTED_LANGUAGES:
        if not onlyMissing or lang not in translation_field:
            translation_field[lang] = get_translation(input_text, lang, CONFIG.DIFY_TRANSLATE_KEY)
            time.sleep(1.5)

    return translation_field


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

    def fetch_event_details(self, event_url: str) -> Dict[str, Any]:
        """
        Fetch details for a specific event
        
        :param event_url: URL of the event
        :return: Transformed event dictionary
        """
        try:
            response = requests.get(event_url)
            response.raise_for_status()
            event_data = response.json()
            
            # Transform event data to desired schema
            transformed_event = {
                'name': event_data.get('name', 'Unnamed Event'),
                'description': event_data.get('description', ''),
                'full_description': event_data.get('description', ''),
                'start': self._parse_datetime(event_data.get('startDate')),
                'end': self._parse_datetime(event_data.get('endDate')),
                'location': self._format_location(event_data.get('location', {})),
                'url': event_data.get('url', ''),
                'img': self._get_event_image(event_data.get('image', {}))
            }
            
            return transformed_event
        
        except requests.RequestException as e:
            self.logger.error(f"Error fetching event details from {event_url}: {e}")
            return {}
        except Exception as e:
            self.logger.error(f"Unexpected error processing event: {e}")
            return {}

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

    def _format_location(self, location: Dict[str, Any]) -> str:
        """
        Format location into a readable string
        
        :param location: Location dictionary from event data
        :return: Formatted location string
        """
        if not location:
            return ''
        
        parts = []
        if name := location.get('name'):
            parts.append(name)
        
        if address := location.get('address', {}):
            address_parts = [
                address.get('streetAddress', ''),
                address.get('addressLocality', ''),
                address.get('addressCountry', '')
            ]
            parts.append(', '.join(filter(bool, address_parts)))
        
        return ', '.join(filter(bool, parts))

    def _get_event_image(self, image: Dict[str, Any]) -> str:
        """
        Extract event image URL
        
        :param image: Image dictionary from event data
        :return: Image URL or empty string
        """
        return image.get('url', image.get('thumbnailUrl', ''))

    def get_all_events(self) -> List[Dict[str, Any]]:
        """
        Fetch and transform all events
        
        :return: List of transformed event dictionaries
        """
        event_urls = self.fetch_event_list()
        events = []
        
        for url in event_urls:
            event = self.fetch_event_details(url)
            if event:
                events.append(event)
        
        self.logger.info(f"Successfully processed {len(events)} events")
        return events


@celery.task(autoretry_for=(RequestException,OperationalError), retry_backoff=True, retry_backoff_max=120, rate_limit="30/m"
)
def fetch_goabase_events(id):
    fetcher = GoabaseEventFetcher()
    all_events = fetcher.get_all_events()
    
    # Pretty print first event for demonstration
    import json
    if all_events:
        print(json.dumps(all_events[0], indent=2))