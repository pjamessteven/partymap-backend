
import json
from pmapi.event.controllers import get_event_or_404
from pmapi.event_artist.controllers import add_artists_to_date

from pmapi.extensions import db
from pmapi.utils import dify_request
from flask import g

from flask.helpers import get_debug_flag
from pmapi.config import DevConfig, ProdConfig
DEV_ENVIRON = get_debug_flag()
CONFIG = DevConfig if DEV_ENVIRON else ProdConfig


def get_lineup_from_text(text):
    result = dify_request(CONFIG.DIFY_LINEUP_KEY, {'lineup_text': text })
    if result:
        result = json.loads(result)
        result =  result.get('items', [])
        return result
    else: 
        return []

def get_lineup_from_image(image_url):
    # can accept base64 or image URL
    if (image_url):
        result = dify_request(CONFIG.DIFY_LINEUP_KEY, {'lineup_image': [{'type': 'image', 'transfer_method': 'remote_url', 'url': image_url}]})
    if result:
        result = json.loads(result)
        return result.get('items', [])
    else: 
        return []
    
def get_lineup_from_image_and_text(event_id, lineup_text, lineup_image_url):
    event = get_event_or_404(event_id)
    next_ed = event.next_event()
    
    lineup = get_lineup_from_text(lineup_text)

    if not lineup or lineup and len(lineup) == 0:
        print('LINEUP getting from img')
        lineup = get_lineup_from_image(lineup_image_url)

    print('LINEUP result: ', lineup)

    if lineup: 
        add_artists_to_date(next_ed, lineup)
        db.session.commit()
    else:
        print('LINEUP not found for ' + event.name)
