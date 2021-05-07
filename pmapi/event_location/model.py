from datetime import datetime
from geoalchemy2.types import Geometry
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects.postgresql import JSONB

from pmapi.extensions import db


event_location_type_association = db.Table(
    "event_location_type_association",
    db.Column("type", db.String, db.ForeignKey("event_location_types.type")),
    db.Column("place_id", db.String, db.ForeignKey("event_locations.place_id")),
)


class EventLocationType(db.Model):
    __tablename__ = "event_location_types"
    type = db.Column(db.String, primary_key=True)
    event_locations = db.relationship(
        "EventLocation",
        secondary="event_location_type_association",
        back_populates="types",
    )


class EventLocation(db.Model):
    __tablename__ = "event_locations"
    place_id = db.Column(db.String, primary_key=True)
    geohash = db.Column(db.String)
    geo = db.Column(Geometry(geometry_type="POINT"))
    name = db.Column(db.String)
    description = db.Column(db.String)
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    country_code = db.Column(db.String)
    country = db.Column(db.String)
    city = db.Column(db.String)
    types = db.relationship(
        "EventLocationType",
        secondary="event_location_type_association",
        back_populates="event_locations",
    )
    address_components = db.Column(JSONB)
    event = db.relationship("Event", back_populates="default_location")
    # event_id = db.Column(db.Integer, db.ForeignKey('events.id'))

    event_dates = db.relationship("EventDate", back_populates="location")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    creator_id = db.Column(UUID, db.ForeignKey("users.id"))
    creator = db.relationship("User", back_populates="created_event_locations")

    # serverside clustering
    cluster_zoom_2_id = db.Column(db.Integer, db.ForeignKey("clusters_2.cluster_id"))
    cluster_zoom_2 = db.relationship("ClusterZoom2", back_populates="locations")
    cluster_zoom_3_id = db.Column(db.Integer, db.ForeignKey("clusters_3.cluster_id"))
    cluster_zoom_3 = db.relationship("ClusterZoom3", back_populates="locations")
    cluster_zoom_4_id = db.Column(db.Integer, db.ForeignKey("clusters_4.cluster_id"))
    cluster_zoom_4 = db.relationship("ClusterZoom4", back_populates="locations")
    cluster_zoom_5_id = db.Column(db.Integer, db.ForeignKey("clusters_5.cluster_id"))
    cluster_zoom_5 = db.relationship("ClusterZoom5", back_populates="locations")
    cluster_zoom_6_id = db.Column(db.Integer, db.ForeignKey("clusters_6.cluster_id"))
    cluster_zoom_6 = db.relationship("ClusterZoom6", back_populates="locations")
    cluster_zoom_7_id = db.Column(db.Integer, db.ForeignKey("clusters_7.cluster_id"))
    cluster_zoom_7 = db.relationship("ClusterZoom7", back_populates="locations")
    cluster_zoom_8_id = db.Column(db.Integer, db.ForeignKey("clusters_8.cluster_id"))
    cluster_zoom_8 = db.relationship("ClusterZoom8", back_populates="locations")
    cluster_zoom_9_id = db.Column(db.Integer, db.ForeignKey("clusters_9.cluster_id"))
    cluster_zoom_9 = db.relationship("ClusterZoom9", back_populates="locations")
    cluster_zoom_10_id = db.Column(db.Integer, db.ForeignKey("clusters_10.cluster_id"))
    cluster_zoom_10 = db.relationship("ClusterZoom10", back_populates="locations")
    cluster_zoom_11_id = db.Column(db.Integer, db.ForeignKey("clusters_11.cluster_id"))
    cluster_zoom_11 = db.relationship("ClusterZoom11", back_populates="locations")
    cluster_zoom_12_id = db.Column(db.Integer, db.ForeignKey("clusters_12.cluster_id"))
    cluster_zoom_12 = db.relationship("ClusterZoom12", back_populates="locations")
    cluster_zoom_13_id = db.Column(db.Integer, db.ForeignKey("clusters_13.cluster_id"))
    cluster_zoom_13 = db.relationship("ClusterZoom13", back_populates="locations")
    cluster_zoom_14_id = db.Column(db.Integer, db.ForeignKey("clusters_14.cluster_id"))
    cluster_zoom_14 = db.relationship("ClusterZoom14", back_populates="locations")
    cluster_zoom_15_id = db.Column(db.Integer, db.ForeignKey("clusters_15.cluster_id"))
    cluster_zoom_15 = db.relationship("ClusterZoom15", back_populates="locations")
    cluster_zoom_16_id = db.Column(db.Integer, db.ForeignKey("clusters_16.cluster_id"))
    cluster_zoom_16 = db.relationship("ClusterZoom16", back_populates="locations")

    def to_dict(self):
        return dict(
            geohash=self.geohash,
            lat=self.lat,
            lon=self.lng,
            name=self.name,
            description=self.description,
            country_code=self.country_code,
            city=self.city,
            place_id=self.place_id,
        )

    def to_point_dict(self):
        return dict(lat=self.lat, lon=self.lng, id=self.geohash)

    def next_event_at_location(self):
        now = datetime.utcnow()
        eventdate = min(self.event_dates, key=lambda x: abs(x.start - now))
        return eventdate.to_dict()


class ClusterZoom2(db.Model):
    __tablename__ = "clusters_2"
    cluster_id = db.Column(db.Integer, primary_key=True)
    count = db.Column(db.Integer)
    centroid = db.Column(Geometry(geometry_type="POINT"))
    locations = db.relationship("EventLocation", back_populates="cluster_zoom_2")


class ClusterZoom3(db.Model):
    __tablename__ = "clusters_3"
    cluster_id = db.Column(db.Integer, primary_key=True)
    count = db.Column(db.Integer)
    centroid = db.Column(Geometry(geometry_type="POINT"))
    locations = db.relationship("EventLocation", back_populates="cluster_zoom_3")


class ClusterZoom4(db.Model):
    __tablename__ = "clusters_4"
    cluster_id = db.Column(db.Integer, primary_key=True)
    count = db.Column(db.Integer)
    centroid = db.Column(Geometry(geometry_type="POINT"))
    locations = db.relationship("EventLocation", back_populates="cluster_zoom_4")


class ClusterZoom5(db.Model):
    __tablename__ = "clusters_5"
    cluster_id = db.Column(db.Integer, primary_key=True)
    count = db.Column(db.Integer)
    centroid = db.Column(Geometry(geometry_type="POINT"))
    locations = db.relationship("EventLocation", back_populates="cluster_zoom_5")


class ClusterZoom6(db.Model):
    __tablename__ = "clusters_6"
    cluster_id = db.Column(db.Integer, primary_key=True)
    count = db.Column(db.Integer)
    centroid = db.Column(Geometry(geometry_type="POINT"))
    locations = db.relationship("EventLocation", back_populates="cluster_zoom_6")


class ClusterZoom7(db.Model):
    __tablename__ = "clusters_7"
    cluster_id = db.Column(db.Integer, primary_key=True)
    count = db.Column(db.Integer)
    centroid = db.Column(Geometry(geometry_type="POINT"))
    locations = db.relationship("EventLocation", back_populates="cluster_zoom_7")


class ClusterZoom8(db.Model):
    __tablename__ = "clusters_8"
    cluster_id = db.Column(db.Integer, primary_key=True)
    count = db.Column(db.Integer)
    centroid = db.Column(Geometry(geometry_type="POINT"))
    locations = db.relationship("EventLocation", back_populates="cluster_zoom_8")


class ClusterZoom9(db.Model):
    __tablename__ = "clusters_9"
    cluster_id = db.Column(db.Integer, primary_key=True)
    count = db.Column(db.Integer)
    centroid = db.Column(Geometry(geometry_type="POINT"))
    locations = db.relationship("EventLocation", back_populates="cluster_zoom_9")


class ClusterZoom10(db.Model):
    __tablename__ = "clusters_10"
    cluster_id = db.Column(db.Integer, primary_key=True)
    count = db.Column(db.Integer)
    centroid = db.Column(Geometry(geometry_type="POINT"))
    locations = db.relationship("EventLocation", back_populates="cluster_zoom_10")


class ClusterZoom11(db.Model):
    __tablename__ = "clusters_11"
    cluster_id = db.Column(db.Integer, primary_key=True)
    count = db.Column(db.Integer)
    centroid = db.Column(Geometry(geometry_type="POINT"))
    locations = db.relationship("EventLocation", back_populates="cluster_zoom_11")


class ClusterZoom12(db.Model):
    __tablename__ = "clusters_12"
    cluster_id = db.Column(db.Integer, primary_key=True)
    count = db.Column(db.Integer)
    centroid = db.Column(Geometry(geometry_type="POINT"))
    locations = db.relationship("EventLocation", back_populates="cluster_zoom_12")


class ClusterZoom13(db.Model):
    __tablename__ = "clusters_13"
    cluster_id = db.Column(db.Integer, primary_key=True)
    count = db.Column(db.Integer)
    centroid = db.Column(Geometry(geometry_type="POINT"))
    locations = db.relationship("EventLocation", back_populates="cluster_zoom_13")


class ClusterZoom14(db.Model):
    __tablename__ = "clusters_14"
    cluster_id = db.Column(db.Integer, primary_key=True)
    count = db.Column(db.Integer)
    centroid = db.Column(Geometry(geometry_type="POINT"))
    locations = db.relationship("EventLocation", back_populates="cluster_zoom_14")


class ClusterZoom15(db.Model):
    __tablename__ = "clusters_15"
    cluster_id = db.Column(db.Integer, primary_key=True)
    count = db.Column(db.Integer)
    centroid = db.Column(Geometry(geometry_type="POINT"))
    locations = db.relationship("EventLocation", back_populates="cluster_zoom_15")


class ClusterZoom16(db.Model):
    __tablename__ = "clusters_16"
    cluster_id = db.Column(db.Integer, primary_key=True)
    count = db.Column(db.Integer)
    centroid = db.Column(Geometry(geometry_type="POINT"))
    locations = db.relationship("EventLocation", back_populates="cluster_zoom_16")
