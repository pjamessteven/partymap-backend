from pmapi.extensions import db
from pmapi.event.model import Event
from sqlalchemy import and_, not_, or_, func
from pmapi.utils import SUPPORTED_LANGUAGES
from datetime import datetime
from pmapi.event_date.model import EventDate
from pmapi.event_tag.model import Tag
from pmapi.event_artist.model import Artist
from pmapi.config import BaseConfig
import requests

import time

from flask.helpers import get_debug_flag
from pmapi.config import DevConfig, ProdConfig

DEV_ENVIRON = get_debug_flag()
CONFIG = DevConfig if DEV_ENVIRON else ProdConfig


def deepseek_translate(text, target_lang, attempt=1, max_attempts=5):
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {CONFIG.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    prompt = f"""Translate the following text to {target_lang}.

IMPORTANT: 
- Return ONLY the translation, nothing else
- If the text is already in the target language or contains no meaningful content, return exactly: TRANSLATION_ERROR
- Do not include quotes, explanations, or any other text

Text to translate:
{text}"""

    data = {
        "model": "deepseek/deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
    }

    try:
        response = requests.post(url, json=data, headers=headers, timeout=60)
        response.raise_for_status()
        json_response = response.json()

        translation = json_response["choices"][0]["message"]["content"].strip()

        if translation == "TRANSLATION_ERROR":
            print(
                f"TRANSLATION_ERROR (already in target lang or do not translate) for: ({target_lang}) {text[:50]}..."
            )
            return None

        return translation

    except Exception as e:
        print(f"Attempt {attempt} failed: {e}")
        if attempt < max_attempts:
            time.sleep(1.5)
            return deepseek_translate(
                text, target_lang, attempt=attempt + 1, max_attempts=max_attempts
            )
        else:
            print("Max attempts reached. Failing.")
            return None


def get_description_translation(text, target_lang):
    if not CONFIG.ENABLE_TRANSLATIONS:
        return None

    result = deepseek_translate(text, target_lang)

    if result and "TRANSLATION_ERROR" in result:
        print(
            "TRANSLATION_ERROR (already in target lang or do not translate) for: ("
            + target_lang
            + ") "
            + text
        )
        return None

    if result:
        print(target_lang + " description: " + result)

    return result


def update_translations():
    print("update_translations:")

    def filter_objects_missing_keys(hstore_column, keys_to_check):
        # Create a condition for each key missing in the hstore column
        conditions = [
            not_(hstore_column.has_key(key))  # Check if the key is missing
            for key in keys_to_check
        ]

        # Include a condition for NULL values in the hstore column
        null_condition = hstore_column.is_(None)

        # Combine the conditions with OR (any key missing or NULL)
        filter_condition = or_(*conditions + [null_condition])
        return filter_condition

    onlyMissing = True

    event_query = db.session.query(Event).filter(
        filter_objects_missing_keys(Event.description_translations, SUPPORTED_LANGUAGES)
    )
    event_query = event_query.join(EventDate)
    # select future events
    event_query = event_query.filter(
        or_(
            and_(
                EventDate.end.is_(None), EventDate.start > func.now()
            ),  # Event.end is NULL and Event.start > NOW()
            EventDate.end > func.now(),  # Event.end is in the future
        )
    )
    event_query = event_query.group_by(Event.id)
    # event_query = event_query.order_by(EventDate.start.asc())

    tags = db.session.query(Tag)
    if onlyMissing:
        tags = tags.filter(
            filter_objects_missing_keys(Tag.tag_translations, SUPPORTED_LANGUAGES)
        )
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
    print(str(event_query.count()) + " events missing translations.")
    for event in event_query:
        print("translating " + event.name)

        DESCRIPTION_AS_SUMMARY = (
            event.description[:20] == event.description[:20]
        )  # save tokens when the description as the summary
        for lang in SUPPORTED_LANGUAGES:
            if event.description_translations is None:
                event.description_translations = {}

            if (
                not DESCRIPTION_AS_SUMMARY
                and lang not in event.description_translations
            ):
                event.description_translations[lang] = get_description_translation(
                    event.description, lang
                )
                event.updated_at = datetime.now()
                time.sleep(1.5)

            if event.full_description_translations is None:
                event.full_description_translations = {}

            if (
                lang not in event.full_description_translations
                and event.full_description
                and len(event.full_description) > 0
            ):
                event.full_description_translations[lang] = get_description_translation(
                    event.full_description, lang
                )

                if DESCRIPTION_AS_SUMMARY and event.full_description_translations[lang]:
                    summary = event.full_description_translations[lang][0:297]
                    if len(summary) > 297:
                        summary += "..."
                    event.description_translations[lang] = summary

                event.updated_at = datetime.now()
                time.sleep(1.5)

        print("translated " + event.name)
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
