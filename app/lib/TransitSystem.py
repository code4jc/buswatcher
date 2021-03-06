from pathlib import Path
import json
import datetime
import geojson
import pickle
import os
import sys
import time

from . import NJTransitAPI, Generators
from .wwwAPI import RouteReport
from .CommonTools import get_config_path
from .DataBases import SQLAlchemyDBConnection, ScheduledStop

class SystemMap:

    def __init__(self):

        # read the /config files -- grades, route metadata and overrides, collection metadata
        try:
            with open(get_config_path() + 'grade_descriptions.json') as f:
                self.grade_descriptions = json.load(f)
            with open(get_config_path() + 'route_descriptions.json') as f:
                self.route_descriptions = json.load(f)
            with open(get_config_path() + 'collection_descriptions.json') as f:
                self.collection_descriptions = json.load(f)
            with open(get_config_path() + 'period_descriptions.json') as f:
                self.period_descriptions = json.load(f)
        except:
            import sys
            sys.exit("<BUSWATCHER>One or more of the config files isn't loading properly")

        # load the route geometries
        self.route_geometries = self.get_route_geometries()
        self.routelist = self.get_routelist()
        self.grade_roster = self.get_grade_roster()

        # create database connection
        self.db = SQLAlchemyDBConnection()


    # def watch_system_map_pickle(self):
    #     # Call this function each time a change happens
    #     def custom_action(text):
    #         self.__reset__()
    #     watch_file = find_pickle_file()
    #     # watcher = Watcher(watch_file)  # simple
    #     watcher = Watcher(watch_file, custom_action, text='pickle file changed, resetting system_map')  # also call custom action function
    #     watcher.watch()  # start the watch going

    def get_route_geometries(self):
        route_geometries={}
        for rd in self.route_descriptions['routedata']:
            # print('getting route geometry for '+rd['route'])
            route_geometries[rd['route']]={
                'route':rd['route'],
                'xml':self.get_single_route_xml(rd['route']),
                'paths': self.get_single_route_Paths(rd['route'])[0],
                'coordinate_bundle': self.get_single_route_Paths(rd['route'])[1]
            }
        return route_geometries

    def get_routelist(self):
        routelist = (list(set(r['route'] for r in self.route_descriptions['routedata'])))
        return routelist

    def get_single_route_xml(self,route):

        try:# load locally
            infile = (get_config_path() + 'route_geometry/' + route +'.xml')
            with open(infile,'rb') as f:
                data = f.read()
                return data

        except: #  if missing download and load
                print ('fetching xmldata for '+route)
                route_xml = NJTransitAPI.get_xml_data('nj', 'routes', route=route)
                outfile = (get_config_path() + 'route_geometry/' + route + '.xml')
                with open(outfile, 'wb') as f:  # overwrite existing file
                    f.write(route_xml)
                infile = (get_config_path() + 'route_geometry/' + route + '.xml')
                with open(infile, 'rb') as f:
                    return f.read()

    def get_single_route_Paths(self, route):
        while True:
            try:
                infile = (get_config_path() + 'route_geometry/' + route + '.xml')
                with open(infile, 'rb') as f:
                    print('parsing Paths for route ' + route)
                    return NJTransitAPI.parse_xml_getRoutePoints(f.read()) # bug trap error here if the XML file is bad (for instance, because the route is inactive like the seasonal 308 route to Great Adventure, 316)
            except:
                pass

    def get_single_route_paths_and_coordinatebundle(self, route):
        routes = self.route_geometries[route]['paths']
        coordinates_bundle = self.route_geometries[route]['coordinate_bundle']
        return routes, coordinates_bundle

    def get_single_route_stoplist_for_localizer(self, route):

        routedata, coordinate_bundle = self.get_single_route_paths_and_coordinatebundle(route)
        stoplist=[]
        for rt in routedata:
            for path in rt.paths:
                for p in path.points:
                    if p.__class__.__name__ == 'Stop':
                        stoplist.append(
                            {'stop_id': p.identity, 'st': p.st, 'd': p.d, 'lat': p.lat, 'lon': p.lon})
        return stoplist

    def get_single_route_stoplist_for_wwwAPI(self, route):
        route_stop_list = []

        for direction in self.get_single_route_Paths(route)[0]:
            path_list = []
            for path in direction.paths:
                stops_points = RouteReport.Path()
                for point in path.points:
                    if isinstance(point, NJTransitAPI.Route.Stop):
                        stops_points.stops.append(point)
                stops_points.id = path.id
                stops_points.d = path.d
                stops_points.dd = path.dd
                path_list.append(
                    stops_points)  # path_list is now a couple of Path instances, plus the metadata id,d,dd fields
            route_stop_list.append(path_list)
            return route_stop_list[0]  # transpose a single copy since the others are all repeats (can be verified by path ids)

    def extract_geojson_features_from_system_map(self, route):
        waypoints_feature = geojson.Feature(geometry=json.loads(self.route_geometries[route]['coordinate_bundle']['waypoints_geojson']))
        stops_feature = geojson.Feature(geometry=json.loads(self.route_geometries[route]['coordinate_bundle']['stops_geojson']))
        return waypoints_feature, stops_feature

    def render_geojson(self, args):

        try:
            # if we only want a single stop geojson
            if 'stop_id' in args.keys():
                # query the db and grab the lat lon for the first record that stop_id matches this one
                with self.db as db:
                    stop_query = db.session.query(
                        ScheduledStop.stop_id,
                        ScheduledStop.lat,
                        ScheduledStop.lon) \
                        .filter(ScheduledStop.stop_id == args['stop_id']) \
                        .first()
                    # format for geojson
                    stop_point = geojson.Point((float(stop_query[2]), float(stop_query[1])))
                    stop_feature = geojson.Feature(geometry=stop_point)
                    return stop_feature

            # otherwise continue to get waypoints/stops for all routes, one route
            elif 'rt' in args.keys():
                waypoints = []
                stops = []
                if args['rt'] == 'all':
                    for r in self.route_descriptions['routedata']:
                        waypoints_item, stops_item = self.extract_geojson_features_from_system_map(r['route'])
                        waypoints.append(waypoints_item)
                        stops.append(stops_item)
                else:
                    waypoints_item, stops_item = self.extract_geojson_features_from_system_map(args['rt'])
                    waypoints.append(waypoints_item)
                    stops.append(stops_item)

            # or a collection of routes
            elif 'collection' in args.keys():
                waypoints = []
                stops = []

                # pick the right collection
                for route in self.collection_descriptions[args['collection']]['routelist']:
                    waypoints_item, stops_item = self.extract_geojson_features_from_system_map(route)
                    waypoints.append(waypoints_item)
                    stops.append(stops_item)

            # now render the layers as geojson
            if args['layer'] == 'waypoints':
                waypoints_featurecollection = geojson.FeatureCollection(waypoints)
                return waypoints_featurecollection
            elif args['layer'] == 'stops':
                stops_featurecollection = geojson.FeatureCollection(stops)
                return stops_featurecollection

            return
        except:
            from flask import abort
            abort(404)
            pass

    def get_grade_roster(self):
        grade_roster=dict()
        for rt in self.routelist:
            report_fetcher = Generators.Generator()
            try:
                grade_report = report_fetcher.retrieve_json(rt, 'grade', 'day')
            except:
                grade_report = {'grade':'N/A'}
            grade_roster[rt]=grade_report['grade']
        return grade_roster




##################################################################
# Class TransitSystem bootstrappers
##################################################################

def flush_system_map():
    system_map_pickle_file = Path("config/system_map.pickle")
    try:
        os.remove(system_map_pickle_file)
        print ('deleted system_map.pickle file')
    except:
        print ('error. could NOT delete system_map.pickle file')
        pass
    return

def find_pickle_file():
    # find the pickle file
    if os.getcwd() == "/":  # docker
        prefix = "/app/app/"
    elif "Users" in os.getcwd():  # osx
        prefix = ""
    else:  # linux & default
        prefix = ""
    pickle_filename = (prefix + "config/system_map.pickle")
    return {'prefix':prefix, 'pickle_filename':pickle_filename}

def load_system_map(**kwargs):
    pickle_filename = find_pickle_file()['pickle_filename']

    # force regen (optional)
    if 'force_regen' in kwargs.keys():
        if kwargs['force_regen'] == True:
            flush_system_map()
            system_map = SystemMap()
            with open(pickle_filename, "wb") as f:
                pickle.dump(system_map, f)

    # if there's a pickle, load it
    try:
        with open(pickle_filename, "rb") as f:
            system_map = pickle.load(f)
            mod_time = datetime.datetime.fromtimestamp(os.path.getmtime(pickle_filename)).strftime('%Y-%m-%d %H:%M:%S')
            print("Loading existing pickle file, last modified at " + mod_time)

    # otherwise regen and load it
    except FileNotFoundError:
        print(str(pickle_filename) + " pickle file not found. Rebuilding, may take a minute or so..")
        system_map = SystemMap()
        with open(pickle_filename, "wb") as f:
            pickle.dump(system_map, f)

    return system_map