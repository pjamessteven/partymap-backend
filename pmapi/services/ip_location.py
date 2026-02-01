from flask import request
from flask.helpers import get_debug_flag
from pmapi.config import BaseConfig as CONFIG

from pmapi import exceptions as exc
import geoip2.database
from pmapi.utils import get_locale

DEV_ENVIRON = get_debug_flag()

reader = geoip2.database.Reader('/app/geoip-data/GeoLite2-City.mmdb')

def get_location_from_ip(ip_address=None):


    if DEV_ENVIRON:
        ip_address = "49.224.108.78"
    elif ip_address is None:
        ip_address = request.remote_addr

    try:
        response = reader.city(ip_address)
        print('locale', get_locale())
        return {
            "country": response.country.names.get(get_locale(), response.country.name),
            "region": response.subdivisions.most_specific.names.get(get_locale(), response.subdivisions.most_specific.name),
            "city": response.city.names.get(get_locale(), response.city.name),
            "lat": response.location.latitude,
            "lon": response.location.longitude,
        }
    except Exception as e:
        print(f"Error fetching geolocation: {e}")
    return {}