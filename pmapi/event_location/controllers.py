import reverse_geocode
import pygeohash as pgh
from pmapi.event_location.model import EventLocation, EventLocationType
from pmapi.extensions import db


def add_new_event_location(**location):

    geometry = location.get('geometry')
    name = location.get('name')
    description = location.get('description')
    place_id = location.get('place_id')
    types = location.get('types')

    lat = float(geometry['location']['lat'])
    lng = float(geometry['location']['lng'])

    geocode = reverse_geocode.search([(lat, lng)])[0]

    location_type_objects = []
    for t in types:
        type = None
        if db.session.query(EventLocationType).filter(
                EventLocationType.type == t).count():
            type = db.session.query(EventLocationType).filter(
                EventLocationType.type == t).one()
        else:
            type = EventLocationType(type=t)
            db.session.add(type)

        location_type_objects.append(type)

    location = EventLocation(geohash=pgh.encode(lat, lng),
                             # For geodetic coordinates,
                             # X is longitude and Y is latitude
                             geo='SRID=4326;POINT ({0} {1})'.format(
                             lng, lat),
                             name=name,
                             description=description,
                             types=location_type_objects,
                             lat=lat,
                             lng=lng,
                             country_code=geocode['country_code'],
                             city=geocode['city'],
                             place_id=place_id)

    # merging - is this ok?
    return db.session.add(location)
    db.session.commit()


def get_event_location(google_place_id):
    return EventLocation.query.get(google_place_id)
