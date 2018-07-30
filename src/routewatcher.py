# fetches the NJT bus locations for all buses currently on a source, route
# and dumps it to mysql database using a table for that line


import sys
import argparse
import datetime

#from src.lib.BusAPI import *
#from src.lib.BusLineDB import *
import lib.BusAPI as BusAPI
import lib.BusRouteLogsDB as BusRouteLogsDB

#
# database setup
# c. table name should be: (approaches) with query to select, or (approaches_30189) ?
#
#
# def db_setup(route):
#
#     db = StopsDB.MySQL('buses', 'buswatcher', 'njtransit')
#     conn = db.conn
#     return conn, db



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--source', dest='source', default='nj', help='source name')
    parser.add_argument('-r', '--route', dest='route', required=True, help='route number')

    # sqlite backend - just requires write privs on the file
    subparsers = parser.add_subparsers()
    sqlite_parser = subparsers.add_parser('sqlite')
    sqlite_parser.add_argument('--sqlite-file', dest='sqlite_file', required=True, help='location of the sqlite file', default=None)

    # script cannot create database
    # requirements: database already exists, or the user specified has CREATE DATABASE privs
    mysql_parser = subparsers.add_parser('mysql') 
    mysql_parser.add_argument('--db-name', dest='db_name', required=True, help='name of the mysql database')
    mysql_parser.add_argument('--db-user', dest='db_user', required=True, help='name of the mysql user')
    mysql_parser.add_argument('--db-pw', dest='db_password', required=False, help='name of the mysql password')
    mysql_parser.add_argument('--db-host', dest='db_host', required=False, default='127.0.0.1', help='host of the mysql database')

    args = parser.parse_args()

    if args.source not in BusAPI._sources:
        print args.source + ' is not a valid source.  Valid sources=' + str(BusAPI._sources.keys())
        sys.exit(-1)
   
    if hasattr(args, 'db_name'):
                db = BusRouteLogsDB.MySQL(args.db_name, args.db_user, args.db_password, args.db_host, args.route)
    elif hasattr(args, 'sqlite_file'): 
        db = BusRouteLogsDB.SQLite(args.sqlite_file, args.route)
    else:
        print 'cannot deduce database type'
        sys.exit(-2)


    now = datetime.datetime.now()
    bus_data = BusAPI.parse_xml_getBusesForRoute(BusAPI.get_xml_data(args.source, 'buses_for_route',route=args.route))
    print bus_data
    db.insert_positions(bus_data, now)



if __name__ == "__main__":
    main()
