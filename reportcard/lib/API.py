import json

import lib.BusAPI as BusAPI
from lib.DataBases import DBConfig, SQLAlchemyDBConnection, Trip, BusPosition, ScheduledStop
from sqlalchemy import func
from sqlalchemy.sql.expression import and_

import geojson
import pandas as pd

import datetime

# on-the-fly-GEOJSON-encoder
def positions2geojson(df):
    features = []
    df.apply(lambda X: features.append(
            geojson.Feature(geometry=geojson.Point((X["lon"],
                                                    X["lat"]    )),
                properties=dict(
                                run=X["run"],
                                op=X["op"],
                                dn=X["dn"],
                                pid=X["pid"],
                                dip=X["dip"],
                                id=X["id"],
                                timestamp=X["timestamp"],
                                fs = str(X["fs"]),
                                pd=str(X["pd"])))
                                    )
                                , axis=1)

    return geojson.FeatureCollection(features)

# positions (real-time and historical)
# /api/v1/positions?rt=87&period={now, daily,yesterday,history}
def get_positions_byargs(args):

    # for NOW, get current positions from NJT API
    if args['period'] == "now":
        positions = BusAPI.parse_xml_getBusesForRoute(BusAPI.get_xml_data('nj', 'buses_for_route', route=args['rt']))
        now = datetime.datetime.now()
        labels = ['bid','lon', 'lat', 'run', 'op', 'dn', 'pid', 'dip', 'id', 'timestamp', 'fs','pd']
        positions_log=pd.DataFrame(columns=labels)

        for bus in positions:
            update = dict()
            for key,value in vars(bus).items():
                if key in labels:
                    if key == 'lat' or key == 'lon':
                        value = float(value)
                    update[key] = value
            update['timestamp'] = now
            positions_log = positions_log.append(update,ignore_index=True)

        try:
            positions_log = positions_log.set_index('timestamp',drop=False)
        except:
            pass

        positions_geojson = positions2geojson(positions_log)

    # for HISTORICAL, get positions from database
    else:
        with SQLAlchemyDBConnection(DBConfig.conn_str) as db:
            today_date = datetime.date.today()
            yesterday = datetime.date.today() - datetime.timedelta(1)
            request_filters = {i: args[i] for i in args if i != 'period'}

            # query into a pandas df

            if args['period'] == "today":
                positions_log = pd.read_sql(db.session.query(BusPosition)
                    .filter_by(**request_filters)
                    .filter(func.date(BusPosition.timestamp) == today_date)
                    .order_by(BusPosition.timestamp.desc())
                    .statement
                    , db.session.bind)

            elif args['period']  == "yesterday":
                positions_log = pd.read_sql(db.session.query(BusPosition)
                    .filter_by(**request_filters)
                    .filter(func.date(BusPosition.timestamp) == yesterday)
                    .order_by(BusPosition.timestamp.desc())
                     .statement
                    , db.session.bind)

            elif args['period']  == "history":
                positions_log = pd.read_sql(db.session.query(BusPosition)
                    .filter_by(**request_filters)
                    .order_by(BusPosition.timestamp.desc())
                    .statement
                    , db.session.bind)

            elif args['period'] is True:
                try:
                    int(args['period']) # check if it digits (e.g. period=20180810)
                    request_date = datetime.datetime.strptime(args['period'], '%Y%m%d') # make a datetime object
                    positions_log = pd.read_sql(db.session.query(BusPosition)
                        .filter_by(**request_filters)
                        .filter(func.date(BusPosition.timestamp) == request_date)
                        .order_by(BusPosition.timestamp.desc())
                        .statement
                        , db.session.bind)
                except ValueError:
                    pass

            # cleanup
            positions_log = positions_log.drop(columns=['cars', 'consist', 'm','pdrtpifeedname','rt','rtrtpifeedname','rtdd','wid1','wid2'])
            positions_geojson = positions2geojson(positions_log)

    return positions_geojson



def _fetch_layers_json(route):
    routes, coordinate_bundle = BusAPI.parse_xml_getRoutePoints(
        BusAPI.get_xml_data('nj', 'routes', route=route))

    # todo collapse these into...
    waypoints_feature = json.loads(coordinate_bundle['waypoints_geojson'])
    waypoints_feature = geojson.Feature(geometry=waypoints_feature)
    stops_feature = json.loads(coordinate_bundle['stops_geojson'])
    stops_feature = geojson.Feature(geometry=stops_feature)

    # todo this?
    # waypoints_feature = geojson.Feature(geometry=json.loads(coordinate_bundle['waypoints_geojson']))
    # stops_feature = geojson.Feature(geometry=json.loads(coordinate_bundle['stops_geojson']))

    return waypoints_feature, stops_feature

# get geoJSON for citywide map
def get_map_layers(args, reportcard_routes):

    waypoints = []
    stops = []

    if args['route'] == 'all':
        for r in reportcard_routes:
            waypoints_item, stops_item = _fetch_layers_json(args['route'])
            waypoints.append(waypoints_item)
            stops.append(stops_item)
    else:
        waypoints_item, stops_item = _fetch_layers_json(args['route'])
        waypoints.append(waypoints_item)
        stops.append(stops_item)

    if args['layer']=='waypoints':
        waypoints_featurecollection = geojson.FeatureCollection(waypoints)
        return waypoints_featurecollection
    elif args['layer']=='stops':
        stops_featurecollection = geojson.FeatureCollection(stops)
        return stops_featurecollection
