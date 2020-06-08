from __future__ import division
import sys, os, string, time, re, getopt, glob, shutil, math
import netCDF4
import numpy as np
import pandas as pd
import csv
import configparser
import argparse
import inspect
from datetime import datetime
from time import perf_counter 
from GeoFlood_Filename_Finder import cfg_finder

# read input NOAA NWM netcdf file
def readForecast(in_nc, df_netmap):
    global comids
    global Qs

    # open netcdf file
    rootgrp = netCDF4.Dataset(in_nc, 'r')
    intype='channel_rt'
    metadata_dims = ['feature_id']
    dimsize = len(rootgrp.dimensions[metadata_dims[0]]) # num rows
    global_attrs={att:val for att,val in rootgrp.__dict__.items()}
    timestamp_str=global_attrs['model_output_valid_time']
    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d_%H:%M:%S') # read
    #timestamp.replace(tzinfo=pytz.UTC) # set timezone 
    t = timestamp.strftime('%Y%m%d_%H%M%S') # reformat timestampe output
    init_timestamp_str=global_attrs['model_initialization_time']
    init_timestamp = datetime.strptime(init_timestamp_str, '%Y-%m-%d_%H:%M:%S') # read
    init_t = init_timestamp.strftime('%Y%m%d_%H%M%S') # reformat timestampe output

    # create attr data for COMID and flowstream attr
    comids_ref = rootgrp.variables['feature_id']
    Qs_ref = rootgrp.variables['streamflow']
    comids = np.copy(comids_ref[:])
    Qs = np.copy(Qs_ref[:])
    comid_used = df_netmap['COMID'].values
    Qs = Qs[np.isin(comids, comid_used)]
    comids = comids[np.isin(comids, comid_used)]
    df_nwm = pd.DataFrame({'COMID':comids, 'Q':Qs})
    df_nwm = pd.merge(df_netmap, df_nwm, on='COMID')
    comids = df_nwm['HYDROID'].values
    Qs = df_nwm['Q'].values
    rootgrp.close() # close netcdf file to save memory

    # check for invalid Qfc
    negCount = 0
    for i in range(Qs.size):
        if Qs[i] < 0.0:
            negCount += 1
    return { 'timestamp': t, 'init_timestamp': init_t}


def forecastH (init_timestr, timestr, hp_input, stage_output):
    global comids
    global Qs
    global h
    
    hpdata = pd.read_csv(hp_input)
    h = np.zeros_like(Qs, dtype=float)
    for i in range(len(comids)):
        #Qs[i] = 510 ### Uvalde: 4247.52705 ### Bastrop: 3433 ### Kimble 6384.3945584048915 ### Harris: 1799.9320627079999 ### Colorado: 4479.3287
        h_array = hpdata[hpdata['CatchId'] == comids[i]]['Stage'].values
        q_array = hpdata[hpdata['CatchId'] == comids[i]]['Discharge (m3s-1)'].values
        h[i] = np.interp(Qs[i], q_array, h_array, right=-9999)
    # save forecast output
    print(q_array.dtype)
    saveForecast(init_timestr, timestr, stage_output) 


def saveForecast(init_timestr, timestr, stage_output):
    global comids
    global Qs
    global h
    # save to netcdf
    rootgrp = netCDF4.Dataset(stage_output, "w", format="NETCDF4")
    rootgrp.Subject = 'Inundation table derived from HAND and NOAA NWM for the rivers of interests'
    rootgrp.Initialization_Timestamp = init_timestr
    rootgrp.Timestamp = timestr
    rootgrp.Description = 'Stage Height lookup table for the HYDROIDs' + \
                          'within the domain of interests through the aggregation' + \
                          'of HAND hydro property tables and NOAA NWM forecast netcdf on channel_rt'
    index = rootgrp.createDimension("index", len(comids))
    comid_vari = rootgrp.createVariable("HYDROID","u4",("index",))
    h_vari = rootgrp.createVariable("H","f4",("index",))
    q_vari = rootgrp.createVariable("Q","f4",("index",))
    comid_vari[:] = comids
    q_vari[:] = Qs
    h_vari[:] = h
    comid_vari.units = 'index'
    comid_vari.long_name = 'Catchment ID (HYDROID)'
    h_vari.units = 'm'
    h_vari.long_name = 'Inundation height forecast'
    q_vari.units = 'm3s-1'
    q_vari.long_name = 'Inundation discharge forecast'
    rootgrp.close()
    csv_output = stage_output[:-3]+".csv"
    df = pd.DataFrame({"HYDROID" : comids, "H" : h, "Q": Qs})
    df.to_csv(csv_output, index=False, columns=['HYDROID', 'Q', 'H'])


# global variables
comids = None # COMID list from NWM forecast table
Qs = None # Q forecast list (discharge) from NWM
h = None # hash table for Q forecast lookup, indexed by COMID (station id)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('nwm',help='Path to NWM input NetCDF',type=str)
    args = parser.parse_args()
    if (args.nwm[-3:]!='.nc'):
    	print('Not a valid NetCDF file or missing .nc extension')
    else:
    	nwmfn = args.nwm 
    geofloodHomeDir,projectName,DEM_name,chunk_status,input_fn,output_fn,hr_status = cfg_finder()
    Name_path_hydro = os.path.join(geofloodHomeDir, output_fn, "Hydraulics",projectName)
    hp_input = os.path.join(Name_path_hydro, "hydroprop-fulltable.csv")  
    Name_path = os.path.join(geofloodHomeDir, output_fn, "GIS", projectName)
    netmap_table = os.path.join(Name_path, DEM_name)+ "_networkMapping.csv"
    df_netmap = pd.read_csv(netmap_table)
    Name_path = os.path.join(geofloodHomeDir, output_fn, "NWM",projectName)
    nwm_current_folder = Name_path
    if not os.path.exists(nwm_current_folder):
        os.mkdir(nwm_current_folder)
    stage_output = os.path.join(nwm_current_folder, os.path.basename(nwmfn))
    tobj = readForecast(nwmfn, df_netmap) # read forecast, set up hash table
    timestr = tobj['timestamp']
    init_timestr = tobj['init_timestamp']
    forecastH(init_timestr, timestr, hp_input, stage_output)