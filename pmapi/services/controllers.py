from flask import request
from flask.helpers import get_debug_flag
from pmapi.config import BaseConfig as CONFIG
import requests

DEV_ENVIRON = get_debug_flag()


def get_location_from_ip():

    if DEV_ENVIRON:
        ip = "172.217.167.110"
    else:
        ip = request.remote_addr

    url = CONFIG.TRACK_USAGE_FREEGEOIP_ENDPOINT.format(ip=ip)
    response = requests.get(url)
    return response.json()
