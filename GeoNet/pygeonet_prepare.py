#! /usr/bin/env python
import os
import shutil
import inspect
import configparser
import sys
"""
File Structure:
geoNetHomeDir : Directory where the following folders/directories will be created.

*Note: [project_name] is either the default project name or user defined project name, not 
actually project_name.

- GeoFlood_[project_name].cfg
- GeoInputs
	- GIS
		- [project_name]
	- Hydraulics
		- [project_name]
	- NWM
		- [project_name]
- GeoOutputs
	- GIS
		- [project_name]
	- Hydraulics
		- [project_name]
	- NWM
		- [project_name]
	- Inundation
		- [project_name]

I'd strongly suggest you keep the file structure as is, but if you are strongly against it
feel free to change it.
"""
# Read pointer cfg file, which points to the project specific cfg file.
config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(os.path.abspath(__file__)),'project_pointer.cfg'))
project_cfg_path = config.get('CFG Directory', 'project_cfg_pointer')

# Read project specific cfg name and define base variables
config2 = configparser.ConfigParser()
config2.read(project_cfg_path)
geoNetHomeDir = config2.get('Section','geofloodhomedir')
projectName = config2.get('Section', 'projectname')
dem_name_text = config2.get('Section', 'dem_name')
inputs_name = config2.get('Section','Input_dir')
outputs_name = config2.get('Section','Output_dir')
demFileName = dem_name_text+".tif"

	
# Create File Structure
parent_dir = [inputs_name,outputs_name]
child_dir = ['GIS','Hydraulics','NWM']
for i in parent_dir:
	for j in child_dir:
		dir = os.path.join(geoNetHomeDir,i,j,projectName)
		if not os.path.exists(dir):
			os.makedirs(dir)
inun_dir = os.path.join(geoNetHomeDir,outputs_name,"Inundation",projectName)
if not os.path.exists(inun_dir):
	os.makedirs(inun_dir)
demDataFilePath = os.path.join(geoNetHomeDir, inputs_name,
       	                      "GIS", projectName)

# Moving COMID Roughness and stage files to the proper directory
geonet3_fp = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
comid_orig_fp = os.path.join(geonet3_fp,'COMID_Roughness.csv')
stage_orig_fp = os.path.join(geonet3_fp,'stage.txt')

comid_target_fp = os.path.join(geoNetHomeDir,inputs_name,"Hydraulics",projectName,"COMID_Roughness.csv")
stage_target_fp = os.path.join(geoNetHomeDir,inputs_name,"Hydraulics",projectName,"stage.txt")

# Copy COMID to project hydraulics directory
if os.path.exists(comid_orig_fp):
	shutil.copyfile(comid_orig_fp,comid_target_fp)
else:
	print("Could not find 'COMID_Roughness.csv")

# Copy stage to project hydraulics directory
if os.path.exists(stage_orig_fp):
	shutil.copyfile(stage_orig_fp,stage_target_fp)
else:
	print("Could not find 'stage.txt")

# Define variables to be used throughout GeoNet/GeoFlood workflow
flowlineMRFileName = 'Flowline.shp'
geonetResultsDir = os.path.join(geoNetHomeDir, outputs_name,
       	                       "GIS", projectName)
geonetResultsBasinDir = os.path.join(geoNetHomeDir, "basinTiffs")

# Write shapefile file paths
shapefilepath = os.path.join(geoNetHomeDir, outputs_name, "GIS", projectName)
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
split_distance=1000
# Skfmm parameters
numBasinsElements = 2

if not os.path.exists(geonetResultsDir):
	os.mkdir(geonetResultsDir)

if __name__=='__main__':
	if os.path.exists(geonetResultsDir):
		print("File Structure Constructed")