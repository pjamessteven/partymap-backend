from flask import request
from pmapi.config import BaseConfig as CONFIG
import requests


def get_location_from_ip():
    url = CONFIG.TRACK_USAGE_FREEGEOIP_ENDPOINT.format(ip=request.remote_addr)
    response = requests.get(url)
    return response.json()
