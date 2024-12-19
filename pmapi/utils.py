import time
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
        'Authorization': f'Bearer {workflow_key}',
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes
        json_response = response.json()
        
        text = json_response['data']['outputs']['text']
        return text

    except Exception as e:
        print(f'Attempt {attempt} failed: {e}')
        if attempt < max_attempts:
            time.sleep(1.5)
            return dify_request(inputs, workflow_key, attempt=attempt + 1, max_attempts=max_attempts)
        else:
            print('Max attempts reached. Failing.')
            print('request url: ' + url )
            print('headers: ', headers)
            print('data:')
            print(data)
            return None

