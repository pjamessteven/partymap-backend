
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


def get_lineup_from_image_and_text(event_id, lineup_text, lineup_image_url):
    event = get_event_or_404(event_id)
    next_ed = event.next_event()
    
    lineup = dify_request(CONFIG.DIFY_LINEUP_KEY, {'lineup_image': [{'type': 'image', 'transfer_method': 'remote_url', 'url': lineup_image_url}], 'lineup_text': lineup_text, 'event_start': event.start_naive })

    if lineup:
        lineup = json.loads(lineup)
        lineup = lineup.get('lineup', [])
        add_artists_to_date(next_ed, lineup)
        db.session.commit()
        print('LINEUP result: ', lineup)

    else:
        print('LINEUP not found for ' + event.name)
