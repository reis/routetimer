#!/usr/bin/env python
# pylint: disable=line-too-long
# pylint: disable-msg=C0103
""" This script updates a TCX file adjusting the timestamps
"""
from lxml import etree
import datetime
import time

# New data to create a new run with a existent route
nstarttime = '2017-07-10 13:30'
ntotaltime = '00:46:43'
nsplit = list()
nsplit.append({'distance': '1400', 'time':'00:09:23'})
nroute = 'GraveyardLoop'

# Reading route
tree = etree.parse('data/routes/{0}.tcx'.format(nroute))
nsmap = {'n': 'http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2'}

# Getting the XML elements to be updated
xname = tree.xpath('/n:TrainingCenterDatabase/n:Courses/n:Course/n:Name', namespaces=nsmap)
xtotaltimeseconds = tree.xpath('/n:TrainingCenterDatabase/n:Courses/n:Course/n:Lap/n:TotalTimeSeconds', namespaces=nsmap)
xdistancemeters = tree.xpath('/n:TrainingCenterDatabase/n:Courses/n:Course/n:Lap/n:DistanceMeters', namespaces=nsmap)
xtrackpoints = tree.xpath('/n:TrainingCenterDatabase/n:Courses/n:Course/n:Track/n:Trackpoint', namespaces=nsmap)
xfirstpoint = xtrackpoints[0]
xlastpoint = xtrackpoints[len(xtrackpoints)-1]

# Calculations
ctotaltime = time.strptime(ntotaltime, '%H:%M:%S')
ctotaltimeseconds = datetime.timedelta(hours=ctotaltime.tm_hour, minutes=ctotaltime.tm_min, seconds=ctotaltime.tm_sec).total_seconds()
cpace = ctotaltimeseconds / float(xdistancemeters[0].text)

# Updating the data for the new TCX file
xname[0].text = 'Running on the {0} route'.format(nroute)
xtotaltimeseconds[0].text = str(ctotaltimeseconds)

# Update time of the first point
xfirstpointtime = xfirstpoint.xpath('n:Time', namespaces=nsmap)
xfirstpointtime[0].text = datetime.datetime.strptime(nstarttime, '%Y-%m-%d %H:%M').strftime('%Y-%m-%dT%H:%M:%S+00:00')

lasttime = xfirstpointtime[0].text
lastdistance = -1
for xpoint in xtrackpoints:
    #print(point)
    xpointtime = xpoint.xpath('n:Time', namespaces=nsmap)
    xpointdistance = xpoint.xpath('n:DistanceMeters', namespaces=nsmap)
    if xpointdistance == 0:
        continue
    deltadistance = float(xpointdistance[0].text) - lastdistance
    xpointtime[0].text = (datetime.datetime.strptime(lasttime, '%Y-%m-%dT%H:%M:%S+00:00') + datetime.timedelta(seconds=deltadistance * cpace)).strftime('%Y-%m-%dT%H:%M:%S+00:00')

    lastdistance = float(xpointdistance[0].text)
    lasttime = xpointtime[0].text

    print(xpointtime[0].text)

# Writing a new file
tree.write('data/runs/file_new.tcx')

