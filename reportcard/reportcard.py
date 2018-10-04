# bus reportcard v1.0
# september 2018 - anthony townsend anthony@bitsandatoms.net

from flask import Flask, render_template, request
from flask_bootstrap import Bootstrap
import lib.ReportCard
import lib.BusAPI
from flask import jsonify

app = Flask(__name__)
Bootstrap(app)


################################################
# APPLICATION DATA IMPORT
################################################

from route_config import reportcard_routes,grade_descriptions



################################################
# STATIC ASSETS
################################################

from flask_assets import Bundle, Environment

bundles = {

    'route_css': Bundle(
        'css/theme.css',
        'css/theme.scss',
        output='gen/route.css'),

}

assets = Environment(app)
assets.register(bundles)


################################################
# WEBSITES
################################################

#1 home page
@app.route('/')
def displayHome():
    # routereport = routereport # setup a dummy for the navbar
    class Dummy():
        def __init__(self):
            self.routename = 'NJTransit' # todo replace with source argument if want to abstract repo for other transit services
    routereport = Dummy()

    return render_template('index.html', reportcard_routes=reportcard_routes, routereport=routereport)

#2 route report - choose service
@app.route('/<source>/<route>')
def genRouteReport_ServicePicker(source, route):
    routereport=lib.ReportCard.RouteReport(source,route,reportcard_routes,grade_descriptions)
    return render_template('route_servicepicker.html', routereport=routereport)

#3 route report - with service
@app.route('/<source>/<route>/service/<service>')
def genRouteReport_ServiceStoplist(source, route, service):
    routereport=lib.ReportCard.RouteReport(source,route,reportcard_routes,grade_descriptions)
    return render_template('route_servicestoplist.html', routereport=routereport,service=service)

# 4 stop report
@app.route('/<source>/<route>/stop/<stop>/<period>')
def genStopReport(source, route, stop, period):
    stopreport = lib.ReportCard.StopReport(route, stop, period)
    hourly_frequency = stopreport.get_hourly_frequency()
    routereport = lib.ReportCard.RouteReport(source, route, reportcard_routes, grade_descriptions)
    predictions = lib.BusAPI.parse_xml_getStopPredictions(lib.BusAPI.get_xml_data('nj', 'stop_predictions', stop=stop, route='all'))
    return render_template('stop.html', stopreport=stopreport, hourly_frequency=hourly_frequency, routereport=routereport, predictions=predictions,period=period)


################################################
# API
################################################

import lib.WebAPI as WebAPI

# @app.route('/api')
# def api_root(rt):
#    print ("You cant fetch all the billions of positions, dum dum.")
#    return


# POSITIONS URL-BASED

# /api/positions/{route}/{period} - returns timestamped positions for an entire route for the period specified
# where period = [today, yesterday, weekly, history, date as 'yyyy-mm-dd' ]
@app.route('/api/v1/positions/<route>/<period>')
def api_positions_route(route,period):
    return WebAPI.get_positions_byurl(route, period)


# POSITIONS ARGS-BASED
# /api/positions?rd=119&period=daily - returns timestamped positions for an entire route for the period specified
# where period = [today, yesterday, weekly, history, date as 'yyyy-mm-dd' ]
@app.route('/api/v1/positions/')
def api_positions2_route():

    args=request.args

    return jsonify(WebAPI.get_positions_byargs(args))

    # return WebAPI.get_positions_byargs(args)








# POSITIONS for a single bus

# /api/positions/{route}/{period}/bus/{v} - returns timestamped positions for an entire route for the period specified
# where period = [today, yesterday, weekly, history, date as 'yyyy-mm-dd' ]
#
@app.route('/api/v1/positions/<route>/<period>/bus/<bus_id>')
def api_positions_v(route,period,bus_id):
    return WebAPI.get_positions_byurl(route, period, v=bus_id)

# ARRIVALS
# /api/arrivals/{route}/{stop}/{period}/
@app.route('/api/arrivals/<route>/<stop>/<period>')
def api_arrivals(route,stop,period):
    return WebAPI.get_arrivals(route,stop,period)



################################################
# ERROR HANDLER
################################################
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error_API_down.html'), 404


################################################
# CUSTOM FILTERS
################################################

@app.template_filter('strftime_today')
def _jinja2_filter_datetime(timestamp, format='%I:%M %p'):
    return timestamp.strftime(format)

@app.template_filter('strftime_period')
def _jinja2_filter_datetime_by_period(timestamp, period):
    if period == "daily":
        format = '%I:%M %p'
    elif period == "yesterday":
        format = '%a %I:%M %p'
    elif period == "weekly":
        format = '%a %I:%M %p'
    elif period == "history":
        format = '%Y-%m-%d %I:%M %p'

    return timestamp.strftime(format)

@app.template_filter('strftime_forever')
def _jinja2_filter_datetime(timestamp, format='%Y-%m-%d %I:%M %p'):
    return timestamp.strftime(format)

@app.template_filter('strftime_timedelta')
def pretty_timedelta(td):
    days = td.days
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if days <> 0:
        pretty_time = ("{a} days {b} hrs {c} mins").format(a=days, b=hours, c=minutes)
        return pretty_time
    elif hours <> 0:
        pretty_time = ("{a} hrs {b} mins").format(a=hours, b=minutes)
        return pretty_time
    else:
        pretty_time = ("{a} mins").format(a=minutes)
    return pretty_time


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)



