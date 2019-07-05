# todo 1 test me with a sudden disconnection

# generator.py
#
# description:
# does hourly, daily RouteReport,StopReport generation to db or json so they don't run on page loads
#
# usage:
# bypasses apscheduler           generator.py --testmode
#                                generator.py
#
#
import argparse, time

from lib.Generators import RouteUpdater, GradeReport, BunchingReport, TraveltimeReport, HeadwayReport
from lib.RouteConfig import load_system_map
from lib.DBconfig import connection_string
from lib.CommonTools import get_config_path

####################################################################3
#   SCHEDULER SETUP
####################################################################3
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor,ProcessPoolExecutor


# figure out context

db_url = get_config_path()

jobstores = {'default': SQLAlchemyJobStore(url='sqlite:///'+db_url)}
# jobstores = {'default': SQLAlchemyJobStore(url=connection_string))} # future move jobstore to mysql db


executors = {'default': ThreadPoolExecutor(20)}
job_defaults = {'coalesce': True, 'max_instances': 5 }

def minutely(system_map):
    # task_trigger_1 = HeadwayReport(system_map)
    print ('minute_tasks just ran')
    return

def quarter_hourly(system_map):
    # task_trigger_1 = TravelTimeReport(system_map)
    print ('quarter_hour_tasks just ran')
    return

def hourly(system_map):
    task_trigger_1 = RouteUpdater(system_map) # refresh route descriptions
    task_trigger_2 = GradeReport().generate_reports(system_map) # refresh letter grades
    print ('hourly_tasks just ran')
    # todo 0 add a delete or rebuild of the system_map.pickle and force tripwatcher.py to reload it
    # e.g. load_system_map(force_regenerate=True)
    return

def daily(system_map):
    # Generators.generate_bunching_report(all) -- once per day at 2am
    task_trigger_1 = BunchingReport().generate_reports(system_map)
    print ('daily_tasks just ran')
    return


if __name__ == "__main__":

    system_map=load_system_map()
    parser = argparse.ArgumentParser()
    parser.add_argument('--testmode', dest='test', action='store_true', help='Test mode, run the scheduled tasks in succession, bypassing apscheduler.')
    parser.add_argument("--tasks", nargs='*', help="List of tasks you want to run")
    # todo all some kind of --setup switch per README that runs all the reports

    args = parser.parse_args()

    if args.test is True:
        for arg in args.tasks:
            func = locals()[arg](system_map)
            func

    else:

        system_map = load_system_map()

        scheduler = BackgroundScheduler(jobstores=jobstores, executors=executors, job_defaults=job_defaults)
        scheduler.add_job(minutely, 'interval', minutes=1, id='every minute', replace_existing=True, args=[system_map])
        scheduler.add_job(quarter_hourly, 'interval', minutes=15, id='every 15 minutes', replace_existing=True, args=[system_map])
        scheduler.add_job(hourly, 'interval', minutes=60, id='every hour', replace_existing=True, args=[system_map])
        scheduler.add_job(daily, 'cron', day='*', hour='2', id='every day at 2am', replace_existing=True, args=[system_map])
        scheduler.start() # todo 0 debug database connection errors https://stackoverflow.com/questions/14207708/ioerror-errno-32-broken-pipe-python
        scheduler.print_jobs()
        print ('generator will sleep now, while tasks run in the background')

        try:
            while True:
                time.sleep(2)
        except (KeyboardInterrupt, SystemExit):
            scheduler.shutdown()

