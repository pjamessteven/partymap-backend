from pmapi.event.model import *
from pmapi.extensions import db
from geoalchemy2 import functions as func
from flask_script import Command
from geoalchemy2.comparator import Comparator
from sqlalchemy.sql import text
from sqlalchemy import or_, and_, cast
from geoalchemy2 import Geometry, func, Geography, WKTElement


class ClusterEventLocations(Command):

    def run(self):
        zoom_level_radius = {
            2: 140000,
            3: 700000,
            4: 400000,
            5: 200000,
            6: 100000,
            7: 50000,
            8: 25000,
            9: 15000,
            10: 7000,
            11: 4000,
            12: 3000,
            13: 2000,
            14: 1000,
            15: 500,
            16: 200
        }
        '''
            2: 700000,
            3: 400000,
            4: 200000,
            5: 100000,
            6: 50000,
            7: 25000,
            8: 15000,
            9: 7000,
            10: 4000,
            11: 3000,
            12: 2000,
            13: 1000,
            14: 500,
            15: 200,
            16: 100
        }
'''
        for zoom_level in zoom_level_radius:
            location = db.session.query(EventLocation).filter(eval('EventLocation.cluster_zoom_'+str(zoom_level)) == None).limit(1).first()
            while location is not None:
                print(zoom_level)
                 # check if there is an existing cluster in radius
                cluster_in_radius = db.session.query(
                                                eval('ClusterZoom'+str(zoom_level)),
                                                ).filter(
                                                     func.ST_DWithin(cast(eval('ClusterZoom'+str(zoom_level)).centroid, Geography(srid=4326)), cast(location.geo, Geography(srid=4326)), zoom_level_radius[zoom_level])
                                                ).order_by(
                                                    Comparator.distance_centroid(eval('ClusterZoom'+str(zoom_level)).centroid,
                                                                 location.geo)
                                                ).limit(1).first()
                if cluster_in_radius is not None:
                    cluster_in_radius.locations.append(location)
                    cluster_in_radius.count = len(cluster_in_radius.locations)
                    # don't think I need to update cluster centroid
                else:
                    locations_in_radius = db.session.query(
                                                    EventLocation,
                                                    ).filter(
                                                        and_(eval('EventLocation.cluster_zoom_'+str(zoom_level)) == None,
                                                            func.ST_DWithin(cast(EventLocation.geo, Geography(srid=4326)), cast(location.geo, Geography(srid=4326)), zoom_level_radius[zoom_level]))
                                                    ).all()
                    centroid = db.session.query(
                                            func.ST_AsText(func.ST_Centroid(func.ST_Union(EventLocation.geo).label('centroid')))
                                            ).filter(
                                                and_(eval('EventLocation.cluster_zoom_'+str(zoom_level)) == None,
                                                    func.ST_DWithin(cast(EventLocation.geo, Geography(srid=4326)), cast(location.geo, Geography(srid=4326)), zoom_level_radius[zoom_level]))
                                            ).all()
                    print(locations_in_radius)
                    print(centroid[0])
                    cluster = eval('ClusterZoom'+str(zoom_level))()
                    cluster.count = len(locations_in_radius)
                    cluster.centroid = WKTElement(centroid[0], srid=4326)
                    cluster.locations = locations_in_radius
                    db.session.add(cluster)

                location = db.session.query(EventLocation).filter(eval('EventLocation.cluster_zoom_'+str(zoom_level)) == None).limit(1).first()

            db.session.commit()
'''


                query = text("""
                    CREATE OR REPLACE FUNCTION make_cluster{0}() RETURNS INTEGER AS\n
                    $$\n
                    DECLARE start_location GEOMETRY;\n
                    DECLARE cluster_id INTEGER;\n
                    DECLARE ids STRING[];\n
                      BEGIN\n
                        SELECT geo INTO start_place FROM event_locations WHERE cluster_zoom_{0} IS NULL limit 1;\n
                        IF start_location is NULL THEN\n
                            RETURN -1;\n
                        END IF;\n
                        SELECT array_agg(geohash) INTO ids FROM event_locations WHERE cluster_zoom_{0} is NULL AND ST_DWithin(start_location, geo, {1});\n
                        INSERT INTO clusters_zoom_2(count, centroid)\n
                        SELECT count(geo), ST_Centroid(ST_Union(geo::geometry)) FROM event_locations, unnest(ids) as location_id\n
                        WHERE geohash = location_id\n
                        RETURN cluster_id;\n
                      END;\n
                    $$  LANGUAGE plpgsql;\n
                        """.format(zoom_level, zoom_level_radius[zoom_level]))

                rs = con.execute(query)
                print(rs)
                query_create_func = query.format(zoom_level, zoom_level_radius[zoom_level])
                query = text("""
                            $do$\n
                            DECLARE cluster_id INTEGER;\n
                            BEGIN\n
                                SELECT 0 INTO cluster_id;\n
                                WHILE cluster_id != -1\n
                                LOOP\n
                                SELECT make_cluster{0}() INTO cluster_id;\n
                                END LOOP;\n
                            END\n
                            $do$;
                            """.format(zoom_level))

                rs = con.execute(query)
                print(rs)


            ids = []
            print(zoom_level)
            locations_without_cluster = db.session.query(EventLocation).filter(
                eval('EventLocation.cluster_zoom_'+str(zoom_level)) == None).all()

            if len(locations_without_cluster) == 0:
                print('no unclustered locations at zoom level {0}'.format(zoom_level))

            else:
                print('clustering {0} locations'.format(len(locations_without_cluster)))
                for location in locations_without_cluster:
                    # find existing cluster within radius
                    exisiting_clusters = db.session.query(
                                            eval('ClusterZoom'+str(zoom_level))
                                            ).filter(
                                                func.ST_DWithin(
                                                    eval('ClusterZoom'+str(zoom_level)).centroid, location.geo, zoom_level_radius[zoom_level])
                                                    )

                    exisiting_cluster = exisiting_clusters.order_by(Comparator.distance_centroid(eval('ClusterZoom'+str(zoom_level)).centroid,
                                location.geo)).limit(1).first()

                    # if there is an existing cluster within radius, add to it
                    if exisiting_cluster:

                        print(exisiting_cluster)
                        # update locations cluster
                        location_cluster = eval('ClusterZoom'+str(zoom_level))
                        print(location_cluster)
                        print(type)

                        # and update centroid of cluster
                        points_in_cluster = []
                        for location in exisiting_cluster.locations:
                            points_in_cluster.append(location.geo)
                        # select cluster_id and centroid as centroid
                        # where cluster_id == exisitng_cluster.cluster_id

                        select_centroid = db.select(
                            [eval('ClusterZoom'+str(zoom_level)).__table__.c.cluster_id, func.ST_Centroid(func.ST_Union(exis.locations)).label('centroid')]
                        ).where(eval('ClusterZoom'+str(zoom_level)).__table__.c.cluster_id==exisiting_cluster.cluster_id)
                        rs = db.engine.execute(select_centroid).fetchall()
                        print(rs)

                        exisiting_cluster.centroid = centroid
                        exisiting_cluster.count += 1
                    else:
                        print('.', end="", flush=True)
                        new_cluster = eval('ClusterZoom'+str(zoom_level))(
                        count = 1,
                        centroid = location.geo
                        )
                        new_cluster.locations.append(location)
                        db.session.add(new_cluster)

                    db.session.commit()
            return
'''
