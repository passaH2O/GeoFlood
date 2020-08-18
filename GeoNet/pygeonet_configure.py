#! /usr/bin/env python
import os
import shutil
import inspect
import configparser
import sys
import argparse

def cmd_inputs():
	parser = argparse.ArgumentParser()
	parser.add_argument('-dir','--geofloodhomedir',help="File path to directory that will hold the cfg file \
			and the inputs and outputs folders. Default is the GeoNet3 directory.",
			type=str)
	parser.add_argument('-p','--project',
			help="Folder within GIS, Hydraulics, and NWM directories \
			of Inputs and Outputs. Default is 'my_project'.",
			type=str)
	parser.add_argument('-n','--DEM_name',
			help="Name of Input DEM (without extension) and the prefix used for all \
			project outputs. Default is 'dem'",
			type=str)
	parser.add_argument('--no_chunk',help="If not passed (Default), DEMs > 1.5 GB will be \
			chunked during Network Extraction. If passed, DEMs will NOT be \
			chunked. In cfg file, 1: Chunk DEMs, 0: Dont chunk DEMs", action='store_true')
	parser.add_argument('--input_dir',help="Name of Inputs folder. Default is 'GeoInputs'.",type=str)
	parser.add_argument('--output_dir',help="Name of Outputs folder. Default is 'GeoOutputs'.",type=str)
	parser.add_argument('--channel_type',help="1: Cost function with NHD HR [BEST]; 0: Cost function with NHD MR (no NHD HR) [2nd BEST]; -1: Cost function with just DEM features [3rd BEST]",
			type=int)
	
	args = parser.parse_args()
	if args.geofloodhomedir:
		home_dir = args.geofloodhomedir
		if os.path.abspath(home_dir) == os.path.dirname(os.path.abspath(__file__)): # check for ".\"
			home_dir = os.getcwd()
		print(' ')
		print('GeoNet and GeoFlood Home Directory for Inputs and Outputs Folder: ')
		print(home_dir)	
	else:
		ab_path = os.path.abspath(__file__)
		home_dir = os.path.dirname(os.path.dirname(ab_path))
		print(' ')
		print('Using default GeoNet and GeoFlood home directory:')
		print(home_dir)

	if args.project:
		project_name=args.project
		print(f"Project Name: {project_name}")
	else:
		project_name='my_project'
		print(f"Default Project Name: {project_name}")
	
	if args.DEM_name:
		dem_name = args.DEM_name
		print(f'DEM Name: {dem_name}')
	else:
		dem_name='dem'
		print(f'Default DEM: {dem_name}')
	if not args.no_chunk:
		print("Chunking DEMs > 1.5 GBs in Network Extraction script")
		chunk = 1
	else:
		print("Not chunking input DEM or its products in Network Extraction script")
		chunk = 0	
	
	if args.input_dir:
		input_directory = args.input_dir
		print(f'Input Folder Name: {input_directory}')
	else:
		input_directory = "GeoInputs"
		print(f'Default Inputs Folder Name: {input_directory}')

	if args.output_dir:
		output_directory = args.output_dir
		print(f'Output Folder Name: {output_directory}')
	else:
		output_directory = "GeoOutputs"
		print(f'Default Outputs Folder Name: {output_directory}')

	if (args.channel_type==1):
		hr_flowline=1
		print("Will attempt to use NHD HR Flowline binary raster in cost function if found in GIS Outputs.")
	elif (args.channel_type!=1) and (args.channel_type!=0) and (args.channel_type!=-1):
		hr_flowline=1
		print("Will attempt to use NHD HR Flowline binary raster in cost function if found in GIS Outputs.")	
	elif args.channel_type==0:
		hr_flowline=0
		print("Will not use NHD HR Flowline raster as a parameter in the network \
			extraction cost function. Will use NHD MR.")
	elif args.channel_type==-1:
		hr_flowline=-1
		print("Only using DEM features in cost function.")		

	config = configparser.ConfigParser()
	config['Section']={'geofloodhomedir':home_dir,
		'projectname':project_name,
		'dem_name':dem_name,
		'Chunk_DEM':chunk,
		'Input_dir':input_directory,
		'Output_dir':output_directory,
		'hr_flowline':hr_flowline}
	cfg_fp = os.path.join(home_dir,'GeoFlood_'+project_name+'.cfg')
	with open(cfg_fp,'w') as configfile:
		config.write(configfile)
	config2 = configparser.ConfigParser()
	config2['CFG Directory']={'project_cfg_pointer':cfg_fp}
	with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'project_pointer.cfg'),'w') as configfile2:
		config2.write(configfile2)

if __name__=='__main__':
	cmd_inputs()
	print ("Configuration Complete")