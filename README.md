# NJ BusWatcher
**updated 2020 mar 6**


## Overview

Buswatcher is a Python web app to collect bus position and stop arrival prediction data from several API endpoints maintained by NJTransit (via vendor Clever Devices), synthesize and summarize this information, and present to riders in a number of useful ways via a simple, interactive web application. Its implemented in Python 3 using flask, SQLalchemy, pandas, and geopandas.

 
## Getting Started

The suite is fully dockerized. Simply grab the repo and install using docker-compose. Manual install instructions in `/doc` folder.
```
cd buswatcher
docker-compose up -d --build
```



## Architecture


### Route Geometry Model

Core classes (see DBconfig.py for formal definitions)
 - A `Trip` represents everything we know about a particular bus making a journey, and is uniquely identified by a string concatenated from the vehicle id, the run number, and the current date. (e.g. `5463_323_20200202`). `Trip` has a one-to-many parent relationship with both `ScheduledStop` and `BusPosition`.
 - A `ScheduledStop` represents a stop along a route, for a particular vehicle, on a particular run. `ScheduledStop` has a many-to-one child relationship with `Trip`. These are created when a `Trip` is created (by `Trip.__init` if I recall).
- A `BusPosition` represents an observation of a bus at a particular point in time.
 `BusPosition` has a many-to-one child relationship with `Trip`.  `BusPosition` has a one-to-one child relationship with `ScheduledStop` (TKverify this).

   

### Components


Everything in `/buswatcher`

These three programs are run by supervisor more or less persistently.

- **www.py** The flask app for routing incoming requests.
- **generator.py**. Batch processor daemon. Has ability to run minutely, hourly, daily tasks. For instance, once a day downloads and pickles route geometry and builds route reports overnight when bus tracking is mostly idle.
- **tripwatcher.py**. Fetches bus current locations for a route from the NJT API, creates a `Trip` instance for each, and populates it with `ScheduledStop` instances for each stop on the service its running, and a `BusPosition` instance for each observed position.

Libraries and config files.

- **/alembic** Database migration files.
- **/config** Top level is user-defined settings. Nothing should break if you change these, but will rebuild.
    -   collection_descriptions.json—define the cities and routes to be tracked by this instance. Ok to change while running.
    -   route_descriptions.json—master definition of routes. bad things happen if you try to track a route not listed here.
    -   period_descriptions.json—labels for the various periods.
    -   grade_descriptions.json—bins and labels for the letter grades.
    - **/reports**—system-generated route reports. dont touch. 
    - **/route_geometry**—system-generated route geometry pickle files. dont touch. 
- **/lib** Core classes.
    - **API.py**—implements the external web API   
    - **DataBases.py**—the ORM models.
    - **DBconfig.py**—user-defined database URL
    - **Generators.py**—classes to create and dump all the various reports for routes/stops/metrics
    - **NJTransitAPI.py**—main fetch and parse from the NJTransit Clever Devices API
    - **RouteScan.py**—main processor for incoming bus positions after pre-processing by NJTransitAPI. Mostly focused on localizing a `BusPosition` instance to the nearest `ScheduledStop`
- **/locust** Load testing stuff.
- **/static** Static stuff served by nginx
    - **/gen**
    - **/images**
    - **/maps** Javascript to render client-size maps
    - **/mdb** CSS stuff
- **/templates** jinja page templates
     
     
### Other stuff

**/dns_updater** Updates domain IP at Gandi.net to host current
**/install** Setup helpers, env config, etc.

  

## API

The maps API is used by the JavaScript maps on the site, and is available for others to use too. Returns current route geometry and vehicle positions as geoJSON. 

URL is `https://www.njbuswatcher.com/api/v1/maps`

`/vehicles?rt=87` Positions of buses currently on the route.

`/waypoints?rt=87` Route geometry as a series of points.

`/stops?rt=87` Stop locations.

## Maintenance
 
Occasionally you may want / need to manually refresh the route reports. 
there will be a need to run the ```generator.py``` daily or hourly batch jobs manually. (For instance after adjusting the grade criteria.) The ```--test``` switch supports this and requires a list of ```--tasks``` as well. e.g. The following commands let you start the job, disown it, send it to the background, and then logout while it continues and finishes on its own.
```bash
$ python generator.py --test --tasks daily hourly
$ disown -h %1
$ bg 1
$ logout
```
Note that the tasks will be run in the order you list them. It's generally recommended to run the longest interval tasks (e.g. daily) first.

## TODOs

#### issues and goals
- There are a number of issues with how we are modeling some of the route geometry and schedule anomalies, that are documented [here](https://github.com/code4jc/buswatcher/issues/19), [here](https://github.com/code4jc/buswatcher/issues/18), and [here](https://github.com/code4jc/buswatcher/issues/17).
- archiving of grades and reports is needed
- graphs would probably be more informative and less processor-heavy than aggreagate stats/summaries for most views
- the API could use some sort of securing/key/token
- the API should expose more useful stuff, including archival data, reports, etc.
- the reporting systems is really burdensome and could use a rethink
- need to add certbot/ssl setup to Getting Started (its jut a few steps. (install certbot + use a different config file for nginx, can copy from current live instance)
- securing netdata is not described here, and it isnt straightforward. we can probably drop it altogether once development winds down and EC2 isntance sizing is more or less finalized.

#### debugging
- `lib/NJTransitAPI.py`
    - `get_xml_data` more graceful failure from longer disconnects -- perhaps a timeout?
- `lib'RouteScan.py`
    - `RouteScan.parse_positions`, automatically add unknown routes to `config/route_descriptions.json`
    - `get_nearest_stop` automatically add unknown routes to route_descriptions.json`
- `tripwatcher.py`
    - graceful fall back to collections only if time to run main_loop is  > 1 min?
- `www.py`
    - `if __name__ == "__main__":` need to figure out how to force flask to check if it needs to reload the pickle file, or do it periodically (possibly in generator minutely_tasks)
- `templates/trip.jinja2` trailing slash breaks url

#### write
- `dash` Replace most of the tables with Dash framework charts (data on mouseover). More attractive and informative, as well as offload processing to the client. [tutorial](https://www.tutorialspoint.com/python_web_development_libraries/python_web_development_libraries_dash_framework.htm)
- `lib/Generators.py`
    - `HeadwayReport`
    - `TraveltimeReport`

#### optimization
would help to do some profiling on `tripwatcher.py` and cythonize particularly slow parts?
- `lib/API.py`
    - `current_buspositions_from_db_for_index()`
    - `__positions2geojson` current is 0.2 seconds per execution on t3a.large
    - `_fetch_positions_df` use less pandas? (each route takes 0.1 to 0.2 seconds, kills the statewide map... maybe process that with its own process on a single buses_all df)
- `lib/Generators.py`
    - `Generator.__init__` create a database session here? self.db =  SQLAlchemyDBConnection(), to inherit the database session from parent class?
    - `RouteUpdater` at step 5, parse all the fields from API response into our data structure
    - `BunchingReport.get_arrivals_here_this_route` is more or less repeated code from `wwwAPI.StopReport.get_arrivals_here_this_route`
- `lib/wwwAPI.py`
    - `get_current_trips` fulfill this with a database query, not fetching from the NJT API, or grab it once and pass it around
    - `StopReport.filter_arrivals` speedup by using slice instead of groupby
    - `TripReport.get_triplog` get this from the database, but how filter... all of the positions for any v seen on this route in the last 10 minutes and not at the last stop?
- `lib'RouteScan.py`
    - `RouteScan.interpolate_missed_stops` this could be moved to `Generator.quarterly_hour_tasks` as a batch job
    - `RouteScan.get_current_trips` filter by current collections routes only? (Eg. discasrd non-active routes)
- `www.py`
    - `GenTripReport` find a better way to get the route metadata than instantiating a whole new RouteReport

#### refactoring
- move other pieces of common code to `lib/CommonTools.py`
- `lib/RouteScan.py
    - `parse_positions` add route # to construction of trip_id, so its concatenated in the form rt_v_run_date and propagate system wide       
    - `ckdnearst` implement haversine for nearest stops
- `generator.py`
    - move jobstore to mysql db
    - make --test and --setup mutually exclusive, and require --tasks if --test is set
    - daily task trigger 4, will this download more limited route points?
- `tripwatcher.py`
    - write an alembic migration for adding the interpolated_arrival_flag column to the db
- `www.py`
    - `displayIndex` replace NJT API call with database call for `vehicle_data, vehicle_count, route_count` to reduce latency
