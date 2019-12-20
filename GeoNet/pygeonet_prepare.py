#! /usr/bin/env python
import os
import shutil
import inspect
import configparser

"""
Folder structure for pyGeoNet is as follows
geoNetHomeDir : defines where files will be written
e.g.
geoNetHomeDir = "C:\\Mystuff\\IO_Data\\"
        --- \\data     (input lidar files will be read from this folder)
        --- \\results  (outputs from pygeonet will be written to this folder)
        --- \\basinTiffs (intermediate GRASS GIS files will be written
                          and deleted from this location. some times these
                          files could be huge, so have enough space)

pmGrassGISfileName -- this is an important intermediate GRASS GIS file name.
# Skfmm parameters
numBasinsElements = 6


#PLEASE DO NOT CHANGE VARIABLES,UNLESS YOU KNOW WHAT YOU ARE DOING

"""

# Prepare GeoNet parameters just prior to main code execution
config = configparser.RawConfigParser()
config.read(os.path.join(os.path.dirname(
    os.path.dirname(
        inspect.stack()[0][1])),
                         'GeoFlood.cfg'))
geoNetHomeDir = config.get('Section', 'geofloodhomedir')
projectName = config.get('Section', 'projectname')
demDataFilePath = os.path.join(geoNetHomeDir, "Inputs",
                               "GIS", projectName)
demFileName = config.get('Section', 'dem_name')+".tif"
channelheadFileName = "Hou_weights.tif"
channeljunctionFileName = "junction.shp"

geonetResultsDir = os.path.join(geoNetHomeDir, "Outputs",
                                "GIS", projectName)
geonetResultsBasinDir = os.path.join(geoNetHomeDir, "basinTiffs")

# Write shapefile file paths
shapefilepath = os.path.join(geoNetHomeDir, "Outputs",
                             "GIS", projectName)
driverName = "ESRI Shapefile"

pointshapefileName = demFileName[:-4]+"_channelHeads"
pointFileName = os.path.join(shapefilepath, pointshapefileName+".shp")

drainagelinefileName = demFileName[:-4]+"_channelNetwork"
drainagelineFileName = os.path.join(shapefilepath, drainagelinefileName+".shp")

junctionshapefileName = demFileName[:-4]+"_channelJunctions"
junctionFileName = os.path.join(shapefilepath, junctionshapefileName+".shp")

streamcellFileName = os.path.join(geonetResultsDir,
                                  demFileName[:-4]+"_streamcell.csv")

xsshapefileName = demFileName[:-4]+"_crossSections"
xsFileName = os.path.join(shapefilepath, xsshapefileName+".shp")

banklinefileName = demFileName[:-4]+"_bankLines"
banklineFileName = os.path.join(shapefilepath, banklinefileName+".shp")


# Things to be changed
# PM Filtered DEM to be used in GRASS GIS for flow accumulation
pmGrassGISfileName = os.path.join(geonetResultsDir, "PM_filtered_grassgis.tif")

# Skfmm parameters
numBasinsElements = 2


# Clean up previous results and recreate output folders
##if os.path.exists(geonetResultsBasinDir):
##    print "Cleaning old basinTiffs"
##    shutil.rmtree(geonetResultsBasinDir)

##if os.path.exists(geonetResultsDir):
##    print "Cleaning old results"
##    shutil.rmtree(geonetResultsDir)
####
####print "Making basinTiffs"
####os.mkdir(geonetResultsBasinDir)
####
print ("Making results")
if not os.path.exists(geonetResultsDir):
    os.mkdir(geonetResultsDir)
