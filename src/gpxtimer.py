#!/usr/bin/env python
# pylint: disable=line-too-long
# pylint: disable-msg=C0103
""" This script updates a GPX file adding timestamps based on a simple chronograph data
"""
from lxml import etree
import datetime
import time
from math import radians, cos, sin, sqrt

# Constant to used to calculate the distance between two points
EARTH_RADIUS = 6370000

# New data to create a new run with a existent route
nstarttime = '2017-07-12 13:00'
ntotaltime = '00:39:55'
ndistancemeters = 7600
nsplits = [{'distance': '1900', 'time':'00:10:25'},\
           {'distance': '3800', 'time':'00:19:58'},
           {'distance': '5700', 'time':'00:30:53'},
           {'distance': '7600', 'time':'00:40:57'},]
nroute = 'Canary Wimbledon'

# Reading route
tree = etree.parse('data/routes/{0}.gpx'.format(nroute))
nsmap = {'n': 'http://www.topografix.com/GPX/1/1'}

# Getting the XML elements to be updated
xname = tree.xpath('/n:gpx/n:trk/n:name', namespaces=nsmap)[0]
xmetadata = tree.xpath('/n:gpx/n:metadata', namespaces=nsmap)[0]
xtrackpoints = tree.xpath('/n:gpx/n:trk/n:trkseg/n:trkpt', namespaces=nsmap)
xfirstpoint = xtrackpoints[0]
xlastpoint = xtrackpoints[len(xtrackpoints)-1]

# Calculate total ditance (now assuming a predefined distance - user has the gps file!)
cdistancemeters = ndistancemeters

# Other calculations
ctotaltime = time.strptime(ntotaltime, '%H:%M:%S')
ctotaltimeseconds = datetime.timedelta(hours=ctotaltime.tm_hour, minutes=ctotaltime.tm_min, seconds=ctotaltime.tm_sec).total_seconds()
cpace = ctotaltimeseconds / float(cdistancemeters)

# Updating the data for the new TCX file
xname.text = 'Running on the {0} route'.format(nroute)

# Insert time in the first point
xfirstpointtime = etree.Element('time')
xfirstpointtime.text = datetime.datetime.strptime(nstarttime, '%Y-%m-%d %H:%M').strftime('%Y-%m-%dT%H:%M:%S+00:00')
xfirstpoint.append(xfirstpointtime)

# Insert time in the metadata to be used like an ID
xmetadatatime = etree.Element('time')
xmetadatatime.text = datetime.datetime.strptime(nstarttime, '%Y-%m-%d %H:%M').strftime('%Y-%m-%dT%H:%M:%S+00:00')
xmetadata.append(xmetadatatime)

# Calculate pace for each split
lastsplitseconds = 0
lastsplitdistance = 0
for split in nsplits:
    splittime = time.strptime(split['time'], '%H:%M:%S')
    split['seconds'] = datetime.timedelta(hours=splittime.tm_hour, minutes=splittime.tm_min, seconds=splittime.tm_sec).total_seconds() - lastsplitseconds
    split['pace'] = split['seconds'] / (float(split['distance']) - lastsplitdistance)

    lastsplitdistance = float(split['distance'])
    lastsplitseconds = split['seconds']

# Set variables with previous element for the loop
partialdistance = 0
lasttime = xfirstpointtime.text
lastlat = float(xfirstpoint.attrib['lat'])
lastlon = float(xfirstpoint.attrib['lon'])
lastele = EARTH_RADIUS + float(xfirstpoint.xpath('n:ele', namespaces=nsmap)[0].text)
currentsplit = 0

# Loop all elements begining on second on to set the time for all points
for xpoint in xtrackpoints[1:]:
    # Get the current point data
    xpointlat = float(xpoint.attrib['lat'])
    xpointlon = float(xpoint.attrib['lon'])
    xpointele = EARTH_RADIUS + float(xpoint.xpath('n:ele', namespaces=nsmap)[0].text)

    # Calculate the distance between two geographic points including altitude
    x0 = xpointele * cos(radians(xpointlat)) * sin(radians(xpointlon))
    y0 = xpointele * sin(radians(xpointlat))
    z0 = xpointele * cos(radians(xpointlat)) * cos(radians(xpointlon))
    x1 = lastele * cos(radians(lastlat)) * sin(radians(lastlon))
    y1 = lastele * sin(radians(lastlat))
    z1 = lastele * cos(radians(lastlat)) * cos(radians(lastlon))
    dist = sqrt((x1-x0)**2 + (y1-y0)**2 + (z1-z0)**2)
    partialdistance += dist

    # Move the to the next split if necessary to get the right pace
    if partialdistance > nsplits[currentsplit]:
        currentsplit += 1

    # Create the time element inside the trkpoint
    xpointtime = etree.Element('time')
    xpointtime.text = (datetime.datetime.strptime(lasttime, '%Y-%m-%dT%H:%M:%S+00:00') + \
                       datetime.timedelta(seconds=dist * nsplits[currentsplit]['pace'] + 0.1)).strftime('%Y-%m-%dT%H:%M:%S+00:00')
    xpoint.append(xpointtime)

    # Update the previous element variables
    lastlat = xpointlat
    lastlon = xpointlon
    lastele = xpointele
    lasttime = xpointtime.text
    xpointtime = None

# Writing a new file
newfile = datetime.datetime.strptime(nstarttime, '%Y-%m-%d %H:%M').strftime('%Y%m%dT%H%M%S') + ' ' + nroute
tree.write('data/runs/{0}.gpx'.format(newfile))

