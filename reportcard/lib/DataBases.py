# ####################################################
# BUSWATCHER
# ####################################################

# -*- coding: utf-8 -*-
import datetime

from sqlalchemy import create_engine, Table, Column, Integer, DateTime, Float, String, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

from lib import BusAPI

# base class
Base = declarative_base()

#####################################################
# CLASS Trip
#####################################################
# stores trip structure for a unique v, run, date
# = list of stops and call times
#####################################################

class Trip(Base):

    def __init__(self, source, route, v,run):
        self.run = run
        self.date = datetime.datetime.today().strftime('%Y-%m-%d')
        self.trip_id=('{v}_{run}_{date}').format(v=v,run=run,date=self.date)

        # populate the stoplist
        stoplist = []
        routes = BusAPI.parse_xml_getRoutePoints(BusAPI.get_xml_data(source, 'buses_for_route', route=route))
        for stop in routes.path.TK:
            if isinstance(Stop):
                stop = ScheduledStop()  # todo create the Trip object
                # append it to a list of stops
                self.stoplist.append(stop)
        # prepare database queue and commit
        session = ScheduledStop.get_session()
        for stop in stoplist:
            session.add(stop)
        session.commit()

    __tablename__ = 'triplog'
    __table_args__ = {'extend_existing': True}
    pkey = Column(Integer(), primary_key=True)
    trip_id = Column(String(255))
    v = Column(Integer())
    run = Column(Integer())
    date = Column(DateTime())
    positions = relationship("BusPosition")
    stops = relationship("ScheduledStop")

    def __repr__(self):
        return "Trip()".format(self=self)

    def get_session(self): # todo abstract this out for all 3

        # db_url = {'drivername': 'postgres',
        #           'username': 'postgres',
        #           'password': 'postgres',
        #           'host': '192.168.99.100',
        #           'port': 5432}
        #
        # engine = create_engine(URL(**db_url))


        engine = create_engine('sqlite:///jc_buswatcher.db')  # todo update engine for real mysql backend
        Session = sessionmaker(bind=engine)

        # try to create tables, just in case they aren't there
        try: # todo smarter check here --> try if table exists == False:
            Base.metadata.create_all(bind=engine)
        except:
            pass

        session = Session()

        return session


################################################################
# CLASS ScheduledStop
################################################################
# represents a stop on a scheduled trip
# used to store final inferred arrival time for a single, v, run, date, stop_id
################################################################
#
class ScheduledStop(Base):

    # def __init__(self):
        # todo set init values for ScheduledStop
        #
        #

    __tablename__ = 'stoplog'
    __table_args__ = {'extend_existing': True}

    pkey = Column(Integer(), primary_key=True)
    trip_id = Column(String(255), ForeignKey('triplog.trip_id'))
    run = Column(Integer())
    v = Column(Integer())
    date = Column(DateTime())
    stop_id = Column(Integer())
    arrival_timestamp = Column(DateTime())

    arrivals = relationship("BusPosition")

    def __repr__(self):
        return "StopCall()".format(self=self)

    def get_session(self):
        # db_url = {'drivername': 'postgres',
        #           'username': 'postgres',
        #           'password': 'postgres',
        #           'host': '192.168.99.100',
        #           'port': 5432}
        #
        # engine = create_engine(URL(**db_url))

        engine = create_engine('sqlite:///jc_buswatcher.db')  # todo update engine for real mysql backend
        Session = sessionmaker(bind=engine)

        # try to create tables, just in case they aren't there
        try:
            Base.metadata.create_all(bind=engine)
        except:
            pass

        session = Session()

        return session


#####################################################
# CLASS BusPosition
#####################################################
# stores raw positions for later reference
#####################################################

class BusPosition(Base):

    #def __init__(self):
        # todo set init values for BusPosition
        #
        #

    __tablename__ ='routelog'
    __table_args__ = {'extend_existing': True}

    pkey = Column(Integer(), primary_key=True)
    lat = Column(Float)
    lon = Column(Float)
    cars = Column(String(20))
    consist = Column(String(20))
    d = Column(String(20))
    dip = Column(String(20))
    dn = Column(String(20))
    fs = Column(String(20))
    id = Column(String(20))
    m = Column(String(20))
    op = Column(String(20))
    pd = Column(String(20))
    pdRtpiFeedName = Column(String(255))
    pid = Column(String(20))
    rt = Column(String(20))
    rtRtpiFeedName = Column(String(20))
    rtdd = Column(String(20))
    rtpiFeedName = Column(String(20))
    run = Column(String(20))
    wid1 = Column(String(20))
    wid2 = Column(String(20))
    timestamp = Column(String(20))

    trip_id = Column(String(255), ForeignKey('triplog.trip_id'))
    stop_id = Column(String(255), ForeignKey('stoplog.stop_id'))
    distance_to_stop = Column(Float())
    arrival_flag = Column(Boolean())

    def __repr__(self):
        line = []
        for prop, value in vars(self).items():
            line.append((prop, value))
        line.sort(key=lambda x: x[0])
        out_string = ' '.join([k + '=' + str(v) for k, v in line])
        return "BusPosition" + '[%s]' % out_string

    def get_session(self):

        # db_url = {'drivername': 'postgres',
        #           'username': 'postgres',
        #           'password': 'postgres',
        #           'host': '192.168.99.100',
        #           'port': 5432}
        #
        # engine = create_engine(URL(**db_url))

        engine = create_engine('sqlite:///jc_buswatcher.db')  # todo update engine for real mysql backend
        Session = sessionmaker(bind=engine)

        # try to create tables, just in case they aren't there
        try:
            Base.metadata.create_all(bind=engine)
        except:
            pass

        session = Session()

        return session







