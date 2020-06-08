from __future__ import division
import os
import pandas as pd
import configparser
import inspect
from time import perf_counter 
from GeoFlood_Filename_Finder import cfg_finder

def main():
    geofloodHomeDir,projectName,DEM_name,chunk_status,input_fn,output_fn,hr_status = cfg_finder()
    Name_path = os.path.join(geofloodHomeDir, output_fn,
                             "Hydraulics", projectName)
    hydropropotxt = os.path.join(Name_path, "hydroprop-basetable.csv")
    manning_n = os.path.join(geofloodHomeDir, input_fn,
                             "Hydraulics", projectName,
                             "COMID_Roughness.csv") 
    handpropotxt = os.path.join(Name_path, "hydroprop-fulltable.csv")
    geofloodResultsDir = os.path.join(geofloodHomeDir, output_fn,
                                      "GIS", projectName)
    Name_path = os.path.join(geofloodResultsDir, DEM_name)
    networkmaptxt = Name_path + "_networkMapping.csv"
    df_result = pd.read_csv(hydropropotxt)
    df_network = pd.read_csv(networkmaptxt)
    if manning_n.isdigit():
        df_result['Roughness'] = manning_n
    else:
        df_n = pd.read_csv(manning_n)
        df_network = pd.merge(df_network, df_n,
                          on='COMID')                      
        df_result = pd.merge(df_result, df_network,
                             left_on='CatchId',
                             right_on='HYDROID')                                          
    df_result = df_result.drop('HYDROID', axis=1).rename(columns=lambda x: x.strip(" "))
    df_result['TopWidth (m)'] = df_result['SurfaceArea (m2)']/df_result['LENGTHKM']/1000
    df_result['WettedPerimeter (m)'] = df_result['BedArea (m2)']/df_result['LENGTHKM']/1000
    df_result['WetArea (m2)'] = df_result['Volume (m3)']/df_result['LENGTHKM']/1000
    df_result['HydraulicRadius (m)'] = df_result['WetArea (m2)']/df_result['WettedPerimeter (m)']
    df_result['HydraulicRadius (m)'].fillna(0, inplace=True)
    df_result['Discharge (m3s-1)'] = df_result['WetArea (m2)']* \
    pow(df_result['HydraulicRadius (m)'],2.0/3)* \
    pow(df_result['SLOPE'],0.5)/df_result['Roughness']
    df_result['FloodAreaRatio'] = df_result['SurfaceArea (m2)']/df_result['AREASQKM']/1000000
    if df_result['Discharge (m3s-1)'].isna().sum() == len(df_result):
    	print('Empty DataFrame, check hydroprop basetable and make sure COMID is in \
    		the COMID_Roughness csv')
    df_result.to_csv(handpropotxt,index=False)


if __name__ == '__main__':
    t0 = perf_counter()
    main()
    t1 = perf_counter()
    print(("time taken to postprocess hydraulic properties:", t1-t0, " seconds"))
