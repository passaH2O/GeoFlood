from __future__ import division
import sys, os, string, time, re, getopt, glob, shutil, math
import netCDF4
import numpy as np
import pandas as pd
from datetime import datetime
import csv
import configparser
import inspect
from time import perf_counter 
#import pytz

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
        Qs[i] = 500
        h_array = hpdata[hpdata['CatchId'] == comids[i]]['Stage'].values
        q_array = hpdata[hpdata['CatchId'] == comids[i]]['Discharge (m3s-1)'].values
        h[i] = np.interp(Qs[i], q_array, h_array, right=-9999)
    # save forecast output
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
    config = configparser.RawConfigParser()
    config.read(os.path.join(os.path.dirname(
        os.path.dirname(
            inspect.stack()[0][1])),
                             'GeoFlood.cfg'))
    geofloodHomeDir = config.get('Section', 'geofloodhomedir')
    projectName = config.get('Section', 'projectname')
    #geofloodHomeDir = "H:\GeoFlood"
    #projectName = "Test_Stream"
    Name_path = os.path.join(geofloodHomeDir, "Outputs",
                             "Hydraulics", projectName)
    hp_input = os.path.join(Name_path, "hydroprop-fulltable.csv")
    Name_path = os.path.join(geofloodHomeDir, "Inputs", "NWM")
    product_type = config.get('Section', 'product_type')
    #product_type = "short_range"
    date = config.get('Section', 'date')
    #date = "180902"
    nwmfn = config.get('Section', 'nwmfn')
    #nwmfn = "nwm.t02z.short_range.channel_rt.f001.conus.nc"
    nwm_input = os.path.join(Name_path, product_type, date, nwmfn)
    DEM_name = config.get('Section', 'dem_name')
    #DEM_name = "DEM"
    Name_path = os.path.join(geofloodHomeDir, "Outputs", "GIS", projectName)
    netmap_table = os.path.join(Name_path, DEM_name)+ "_networkMapping.csv"
    df_netmap = pd.read_csv(netmap_table)
    Name_path = os.path.join(geofloodHomeDir, "Outputs", "NWM")
    nwm_current_folder = os.path.join(Name_path, product_type, date)
    if not os.path.exists(nwm_current_folder):
        os.mkdir(nwm_current_folder)
    stage_output = os.path.join(nwm_current_folder, nwmfn)
    tobj = readForecast(nwm_input, df_netmap) # read forecast, set up hash table
    timestr = tobj['timestamp']
    init_timestr = tobj['init_timestamp']
    forecastH(init_timestr, timestr, hp_input, stage_output)

