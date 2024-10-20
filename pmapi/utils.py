import random
import string


ROLES = {"UNPRIVILIGED_USER": 0, "HOST": 10, "STAFF": 20, "ADMIN": 30}

ACCOUNT_STATUSES = ["active", "disabled", "pending"]

chars = string.ascii_letters + string.digits


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

