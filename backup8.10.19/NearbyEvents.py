import collections, csv, logging, os, sys, zipfile
csv.field_size_limit(sys.maxsize)
from scipy.spatial import cKDTree as KDTree
import numpy as np
from pmapi.models.Event import *
from sklearn.neighbors.dist_metrics import DistanceMetric
from sklearn.neighbors import BallTree
from pmapi.application import db
import math

class NearbyEvents:

    def __init__(self):
        self.geocode_filename='eventlocations.csv'
        coordinates, self.eventids = self.extract()
        print(coordinates)
        self.tree = BallTree(coordinates, metric=DistanceMetric.get_metric('haversine'))
        self.numberOfEvents = coordinates.shape[0]

    def extract(self):
        """Extract geocode data from zip
        """
        if os.path.isfile(self.geocode_filename):
            print('compact nearbyevents CSV found')
            # open compact CSV
            rows = csv.reader(open(self.geocode_filename))
        else:
            print('updating nearbyevents CSV')
            rows = self.updateCSV()

        # load a list of known coordinates and corresponding locations
        coordinates, eventids = [], []
        for lat, lng, eventId in rows:
            coordinates.append([float(lat), float(lng)])
            eventids.append(eventId)
        coordinates = np.array(coordinates)
        return coordinates, eventids

    #should run this every time an event is added
    def updateCSV(self):
        # extract coordinates into more compact CSV for faster loading
        writer = csv.writer(open(self.geocode_filename, 'w'))
        rows = []

        events = EventDate.query.all()
        for e in events:
            event = e.to_dict()
            lat = np.radians(float(event['lat']))
            lng = np.radians(float(event['lng']))
            eventId = event['id']
            row = lat, lng, eventId
            writer.writerow(row)
            rows.append(row)
        return rows

    def addEventToCSV(lat, lng, id):
        writer = csv.writer(open('eventlocations.csv', 'a'))
        lat = np.radians(float(lat))
        lng = np.radians(float(lng))
        eventId = id
        row = lat, lng, eventId
        writer.writerow(row)

    def query(self, searchcoordinate, current_user):
        """Find closest match to this list of coordinates
                    print(coordinates)
        """
        lat = np.radians(float(searchcoordinate[0][0]))
        lng = np.radians(float(searchcoordinate[0][1]))

        if self.numberOfEvents < 30:
            resultsToReturn = self.numberOfEvents
        else:
            resultsToReturn = 30
        try:
            distances, indices = self.tree.query([(lat,lng)], k=resultsToReturn)
        except ValueError as e:
            logging.info('Unable to parse coordinates: {}'.format(searchcoordinate))
            raise e
        else:
            #need to multiply disctance result by 6371 (mean radius of the earth) to get kms
            results = [(self.eventids[val], distances[0][index]*6371) for index, val in enumerate(indices[0])]
            print(results)
            resultevents = []
            for eventid, distance in results:
                print(eventid, distance)
                event = EventDate.query.get(eventid).to_dict()
                event['distance']=int(distance)
                print(event)
                resultevents.append(event)

            return resultevents

    def search(coordinates, current_user = None):
        """Search for closest known events to these coordinates
        """
        nb = NearbyEvents()
        return nb.query(coordinates, current_user)
