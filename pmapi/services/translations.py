from pmapi.extensions import db
from pmapi.event.model import Event
from sqlalchemy import and_, not_, or_
from pmapi.utils import SUPPORTED_LANGUAGES, get_description_translation
from datetime import datetime
from pmapi.event_date.model import EventDate
from pmapi.event_tag.model import  Tag
from pmapi.event_artist.model import  Artist
from pmapi.config import BaseConfig

import time
def update_translations():
    print('updating')
    def filter_objects_missing_keys(hstore_column, keys_to_check):
        # Create a condition for each key
        conditions = [
            not_(hstore_column.has_key(key))
            for key in keys_to_check
        ]

        # Combine conditions with OR (any key missing)
        filter_condition = or_(*conditions)
        return filter_condition

    onlyMissing = True

    event_query = db.session.query(Event).filter( filter_objects_missing_keys(Event.description_translations, SUPPORTED_LANGUAGES))
    event_query = event_query.join(EventDate)
    event_query = event_query.filter(EventDate.end >= datetime.now())
    event_query = event_query.order_by(EventDate.start_naive.asc())

    tags = db.session.query(Tag)   
    if onlyMissing:
        tags = tags.filter(filter_objects_missing_keys(Tag.tag_translations, SUPPORTED_LANGUAGES))
    tags = tags.filter(Tag.count > 2)

    artists = db.session.query(Artist).all()
    """
    for tag in tags.all()[:10]:
        for lang in SUPPORTED_LANGUAGES:
            if not onlyMissing or lang not in tag.tag_translations:
                tag.tag_translations[lang] = get_description_translation(tag.tag, lang)
                time.sleep(1.5)
        print('translated ' + tag.tag)
        print(tag.tag_translations)
        db.session.commit()
    """
    for event in event_query:
        for lang in SUPPORTED_LANGUAGES:
            if lang not in event.description_translations:
                event.description_translations[lang] = get_description_translation(event.description, lang)
                time.sleep(1.5)
            if lang not in event.full_description_translations and event.full_description and len(event.full_description) > 0 :
                event.full_description_translations[lang] = get_description_translation(event.full_description, lang)
                time.sleep(1.5)
        print('translated ' + event.name)
        db.session.commit()

    """
    for artist in artists[:10]:
        for lang in SUPPORTED_LANGUAGES:
            if artist.description and len(artist.description) > 0:
                artist.description_translations[lang] = get_description_translation(artist.description, lang)
                time.sleep(1.5)
            if artist.disambiguation and len(artist.disambiguation) > 0:
                artist.disambiguation_translations[lang] = get_description_translation(artist.disambiguation, lang)
                time.sleep(1.5)
        if artist.description or artist.disambiguation:
            print('translated ' + artist.name)
        else: 
            print('skipped ' + artist.name + ' - no content to translate')
    """