from datetime import time
import json
import random
import string
from pmapi.config import BaseConfig
import requests
from flask import request, g
from flask.helpers import get_debug_flag
from .config import DevConfig, ProdConfig
DEV_ENVIRON = get_debug_flag()
CONFIG = DevConfig if DEV_ENVIRON else ProdConfig



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


def dify_request(inputs, workflow_key, attempt=1, max_attempts=5):
    url = f'{BaseConfig.DIFY_URL}/workflows/run'
    
    data = {
        'inputs': inputs,
        'response_mode': 'blocking',
        'user': BaseConfig.DIFY_USER
    }
    
    headers = {
        'Authorization': f'Bearer {workflow_key}'
    }

    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes
        json_response = response.json()
        try:
            text = json_response['data']['outputs']['text']
        except (KeyError, TypeError):
            text = None
        return text

    except Exception as e:
        print(f'Attempt {attempt} failed: {e}')
        if attempt < max_attempts:
            return dify_request(inputs, workflow_key, attempt=attempt + 1, max_attempts=max_attempts)
        else:
            print('Max attempts reached. Failing.')
            return None


def get_description_translation(text, target_lang):
    result = dify_request({'text': text, 'target_lang': target_lang}, CONFIG.DIFY_TRANSLATE_KEY)

    if result and 'TRANSLATION_ERROR' in result:
        print('TRANSLATION_ERROR (already in target lang or do not translate) for: (' + target_lang + ') ' + text)
        return None 

    print(target_lang + ' description: ', + result)

    return result    


def get_lineup_from_text(text):
    result = dify_request({'lineup_text': text }, CONFIG.DIFY_LINEUP_KEY)
    if result:
        result = json.loads(result)
        result =  result.get('items', [])
        print('lineup result: ', + result)
        return result
    else: 
        return []

def get_lineup_from_image(image):
    # can accept base64 or image URL
    result = dify_request({'lineup_image': image}, CONFIG.DIFY_LINEUP_KEY)
    if result:
        result = json.loads(result)
        return result.get('items', [])
    else: 
        return []