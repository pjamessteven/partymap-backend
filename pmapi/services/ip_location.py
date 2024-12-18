from flask import request
from flask.helpers import get_debug_flag
from pmapi.config import BaseConfig as CONFIG
import requests
from requests.exceptions import RequestException
import logging
from pmapi import exceptions as exc

DEV_ENVIRON = get_debug_flag()


def get_location_from_ip():

    if DEV_ENVIRON:
        ip = "103.235.93.111"
    else:
        ip = request.remote_addr

    url = CONFIG.TRACK_USAGE_FREEGEOIP_ENDPOINT.format(ip=ip)

    try:
        response = requests.get(url)
    except RequestException as e:
        logging.error(
            "services.get_location_from_ip.request_error",
            #  exception=e,
        )
        raise exc.UpstreamError(
            message="Couldn't get your rough location")

    return response.json()
