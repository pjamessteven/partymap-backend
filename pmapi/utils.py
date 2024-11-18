from datetime import time
import random
import string
from pmapi.config import BaseConfig
import requests
from flask import request, g


ROLES = {"UNPRIVILIGED_USER": 0, "HOST": 10, "STAFF": 20, "ADMIN": 30}

ACCOUNT_STATUSES = ["active", "disabled", "pending"]

chars = string.ascii_letters + string.digits

SUPPORTED_LANGUAGES = ['en', 'zh-tw', 'zh-cn', 'ru', 'ja', 'fr', 'es', 'it', 'de', 'pt', 'pt-br', 'nl', 'pl', 'hi'] 

def random_string(length=32):
    return "".join(random.SystemRandom().choice(chars) for _ in range(length))

def normalize_bounds(bounds):
    northEast = bounds['_northEast']
    southWest = bounds['_southWest']

    def normalize_longitude(lng):
        return ((lng + 180) % 360) - 180

    normalized_bounds = {
        '_northEast': {
            'lng': normalize_longitude(northEast['lng']),
            'lat': min(90, max(-90, northEast['lat']))
        },
        '_southWest': {
            'lng': normalize_longitude(southWest['lng']),
            'lat': min(90, max(-90, southWest['lat']))
        }
    }
    return normalized_bounds

def get_locale():
    lang_preference = request.headers.get('lang')
    # if a user is logged in, use the locale from the user settings
    user = getattr(g, 'user', None)
    if user is not None:
        return user.locale
    elif lang_preference:
        return lang_preference   
    # otherwise try to guess the language from the user accept
    # header the browser transmits.  We support de/fr/en in this
    # example.  The best match wins.
    return request.accept_languages.best_match(SUPPORTED_LANGUAGES)


def get_translation_for_all_languages(text, target_translation_dict):
    for lang in SUPPORTED_LANGUAGES:
        if lang not in target_translation_dict:
            target_translation_dict[lang] = get_translation(text, lang, BaseConfig.DIFY_TRANSLATE_TAG_KEY)
            time.sleep(1.5)
    print('translation complete:', target_translation_dict)
    return target_translation_dict

def get_translation(text, target_lang, workflow_key):
    url = f'{BaseConfig.DIFY_URL}/workflows/run'
    
    data = {
        'inputs': {'text': text, 'target_lang': target_lang},
        'response_mode': 'blocking',
        'user': BaseConfig.DIFY_USER
    }
    
    headers = {
        'Authorization': 'Bearer ' + workflow_key
    }

    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes
        json =  response.json()
        text = json['data']['outputs']['text']
        print('text', json, text)
        if 'TRANSLATION_ERROR' in text:
            print('TRANSLATION_ERROR (already in target lang or do not translate) for: (' + target_lang + ') ' + text)
            return None 
        return text
    
    except Exception as e:
        # Handle any request exceptions
        print(e)
        return None
