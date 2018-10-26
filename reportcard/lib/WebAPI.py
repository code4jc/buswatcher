# handles the API for the bustracker app itself

from . import BusRouteLogsDB
from . import BusAPI
from .ReportCard import timestamp_fix
import geojson
import pandas as pd
import datetime

try:
    db_state = os.environ['REPORTCARD_PRODUCTION']
    db_server = '192.168.1.181'
except:
    db_server = '127.0.0.1'


def data2geojson(df):
    features = []
    df.apply(lambda X: features.append(
            geojson.Feature(geometry=geojson.Point((X["lon"],
                                                    X["lat"]    )),
                properties=dict(bid=X["bid"],
                                run=X["run"],
                                op=X["op"],
                                dn=X["dn"],
                                pid=X["pid"],
                                dip=X["dip"],
                                id=X["id"],
                                timestamp=X["timestamp"],
                                fs = str(X["fs"].decode('utf8')),
                                pd=str(X["pd"].decode('utf8'))))
                                    )
            , axis=1)


    return geojson.FeatureCollection(features)



def get_positions_byargs(args):

    # database initialization
    db = BusRouteLogsDB.MySQL('buses', 'buswatcher', 'njtransit', db_server, args['rt'])
    conn = db.conn

    table_name = 'routelog_' + args['rt']


    sql_insert=str()
    for key, value in list(args.items()):
        if key == 'period':
            pass
        else:
            _sql_snippet = (" AND {}={}").format(key,value)
            sql_insert+=_sql_snippet
    sql_insert=("("+sql_insert+")")

    # NOW - get current positions from NJT API and setup as a dataframe like others
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
            print(":)")
        except:
            print("!!")

        # positions_log = timestamp_fix(positions_log)
        positions_geojson = data2geojson(positions_log)

    # HISTORICAL GET FROM DB
    else:
        if args['period'] == "daily":
            query = ('SELECT * FROM %s WHERE (%s AND DATE(`timestamp`)=CURDATE() ) ORDER BY timestamp DESC;' % (table_name, sql_insert))
        elif args['period']  == "yesterday":
            query = ('SELECT * FROM %s WHERE (%s AND (timestamp >= CURDATE() - INTERVAL 1 DAY AND timestamp < CURDATE())) ORDER BY timestamp DESC;' % (table_name, sql_insert))
        elif args['period']  == "weekly":
            query = ('SELECT * FROM %s WHERE (%s AND (YEARWEEK(`timestamp`, 1) = YEARWEEK(CURDATE(), 1))) ORDER BY timestamp DESC;' % (table_name, sql_insert))
        elif args['period']  == "history":
            query = ('SELECT * FROM %s WHERE %s ORDER BY timestamp DESC;' % (table_name, sql_insert))

        # elif kwargs['period']  like "2018-08-10":
            # query = ('SELECT * FROM %s WHERE (%s AND DATE(`timestamp`)=("2018-08-10") ORDER BY timestamp DESC;' % (table_name, sql_insert))

        # remove the leading AND in query
        query = query.replace(' AND ', '', 1)

        # get data and basic cleanup
        positions_log = pd.read_sql_query(query, conn)
        positions_log = positions_log.drop(columns=['cars', 'consist', 'm','pdRtpiFeedName','rt','rtRtpiFeedName','rtdd','wid1','wid2'])

        positions_log = timestamp_fix(positions_log)

        positions_geojson = data2geojson(positions_log)

    return positions_geojson
