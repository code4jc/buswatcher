###########################################################################
# Localizer
###########################################################################

import datetime, time, collections

import pandas as pd
import numpy as np
from functools import lru_cache

import geopandas
from scipy.spatial import cKDTree
from shapely.geometry import Point

from . import DataBases, BusAPI
from buswatcher.lib.RouteConfig import load_route_geometry

# @lru_cache() # todo 0 not sure cache is doing anything
# # todo 0 alt cache method would be to get the route points in RouteConfig.maintenance_check and then just load them here, or load themi ntripwatcher and pass them into Localizer with each call -- if do this make sure to exploit it everywhere else we are fetching that same data
# def memoized_fetch_routedata(route, ttl_hash=None):
#     routedata, coordinates_bundle = BusAPI.parse_xml_getRoutePoints(BusAPI.get_xml_data('nj', 'routes', route=route))
#     return routedata
#
# def get_ttl_hash(seconds=3600):
#     """Return the same value withing `seconds` time period"""
#     return round(time.time() / seconds)



###########################################################################
# CKDNEAREST
# https://gis.stackexchange.com/questions/222315/geopandas-find-nearest-point-in-other-dataframe
# Here is a helper function that will return the distance and 'Name'
# of the nearest neighbor in gpd2 from each point in gpd1.
# It assumes both gdfs have a geometry column (of points).
###########################################################################

def ckdnearest(gdA, gdB, bcol):
    nA = np.array(list(zip(gdA.geometry.x, gdA.geometry.y)) )
    nB = np.array(list(zip(gdB.geometry.x, gdB.geometry.y)) )
    btree = cKDTree(nB)
    dist, idx = btree.query(nA,k=1)

    # CONVERSION OF DEGREES TO FEET

    # current crude method, 1 degree = 69 miles = 364,320 feet
    df = pd.DataFrame.from_dict({'distance': (dist.astype(float)*364320),bcol : gdB.loc[idx, bcol].values })

    # # new method based on https://gis.stackexchange.com/questions/279109/calculate-distance-between-a-coordinate-and-a-county-in-geopandas
    # from math import radians, cos, sin, asin, sqrt
    #
    # def haversine(lon1, lat1, lon2, lat2):
    #     # Calculate the great circle distance between two points on the earth (specified in decimal degrees)
    #     lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    #     dlon = lon2 - lon1
    #     dlat = lat2 - lat1
    #     a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    #     c = 2 * asin(sqrt(a))
    #     r = 3956  # Radius of earth in miles. Use 6371 for kilometers
    #     return c * r
    #
    # df = pd.DataFrame.from_dict({'distance': (haversine(gdA.geometry.x, gdA.geometry.y, gdB.geometry.x, gdB.geometry.y)),bcol : gdB.loc[idx, bcol].values })
    #
    # # EXAMPLE OF ITERATING OVER A GDF
    # # for index, row in gdf.iterrows():
    # #     for pt in list(row['geometry'].exterior.coords):
    #

    return df




###########################################################################
# GET_NEAREST_STOP
#
# Finds the nearest stop, distance to it, from each item in a list of Bus objects.
# Returns as a list of BusPosition objects.
#
###########################################################################

def get_nearest_stop(buses,route):

    # sort bus data into directions

    buses_as_dicts = [b.to_dict() for b in buses]
    result2 = collections.defaultdict(list)

    for b in buses_as_dicts:
        result2[b['dd']].append(b)
    buses_by_direction = list(result2.values())

    if len(buses) == 0:
        bus_positions = []
        return bus_positions

    # acquire and sort stop data in directions (ignoring services)

    # routedata, coordinates_bundle = BusAPI.parse_xml_getRoutePoints(BusAPI.get_xml_data('nj', 'routes', route=route))
    routedata = BusAPI.parse_xml_getRoutePoints(load_route_geometry(route))

    stoplist = []
    for rt in routedata:
        for path in rt.paths:
            for p in path.points:
                if p.__class__.__name__ == 'Stop':
                    stoplist.append(
                        {'stop_id': p.identity, 'st': p.st, 'd': p.d, 'lat': p.lat, 'lon': p.lon})

    result = collections.defaultdict(list)
    for d in stoplist:
        result[d['d']].append(d)
    stops_by_direction = list(result.values())

    # loop over the directions in buses_by_direction

    bus_positions = []

    for bus_direction in buses_by_direction: #

        # create bus geodataframe
        #df1 = pd.DataFrame.from_records([b.to_dict() for b in buses])
        df1 = pd.DataFrame.from_records(bus_direction)
        df1['lat'] = pd.to_numeric(df1['lat'])
        df1['lon'] = pd.to_numeric(df1['lon'])
        df1['coordinates'] = list(zip(df1.lon, df1.lat))
        df1['coordinates'] = df1['coordinates'].apply(Point)
        gdf1 = geopandas.GeoDataFrame(df1, geometry='coordinates')

        # create stop geodataframe

        # turn stops_by_direction into a dict with:
        # pandas.DataFrame.from_records([s.to_dict() for s in signals])

        for stop_direction in stops_by_direction:
            if bus_direction[0]['dd'] == stop_direction[0]['d']:

                df2=pd.DataFrame.from_records(stop_direction)
                df2['lat'] = pd.to_numeric(df2['lat'])
                df2['lon'] = pd.to_numeric(df2['lon'])

                df2['coordinates'] = list(zip(df2.lon, df2.lat))
                df2['coordinates'] = df2['coordinates'].apply(Point)
                gdf2 = geopandas.GeoDataFrame(df2, geometry='coordinates')

                # call localizer
                inferred_stops = ckdnearest(gdf1, gdf2, 'stop_id')

                gdf1['stop_id'] = inferred_stops['stop_id']
                gdf1['distance'] = inferred_stops['distance']


                # serialize as a list of BusPosition objects

                bus_list = []

                for index, row in gdf1.iterrows():
                    position = DataBases.BusPosition()

                    position.lat = row.lat
                    position.lon = row.lon
                    position.cars = row.cars
                    position.consist = row.consist
                    position.d = row.d
                    # position.dip = row.dip
                    position.dn = row.dn
                    position.fs = row.fs
                    position.id = row.id
                    position.m = row.m
                    position.op = row.op
                    position.pd = row.pd
                    position.pdrtpifeedname = row.pdRtpiFeedName
                    position.pid = row.pid
                    position.rt = row.rt
                    position.rtrtpifeedname = row.rtRtpiFeedName
                    position.rtdd = row.rtdd
                    position.rtpifeedname = row.rtpiFeedName
                    position.run = row.run
                    position.wid1 = row.wid1
                    position.wid2 = row.wid2

                    position.trip_id = ('{id}_{run}_{dt}').format(id=row.id, run=row.run, dt=datetime.datetime.today().strftime('%Y%m%d'))
                    position.arrival_flag = False
                    position.distance_to_stop = row.distance
                    position.stop_id = row.stop_id
                    position.timestamp = datetime.datetime.now()

                    bus_list.append(position)

                bus_positions.append(bus_list)

            else:
                pass



    return bus_positions
