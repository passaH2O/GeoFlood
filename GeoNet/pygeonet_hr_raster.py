from __future__ import division
import numpy as np
import geopandas as gpd
import rasterio
import argparse
from time import perf_counter 
from pygeonet_rasterio import *
from pygeonet_plot import *
from rasterio import features


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("HR_Flowline",help="File path to HR Shapefile. Make sure all other \
    			metadata related files for the shapefile are in the same location.",
    			type=str)
    args = parser.parse_args()
    flowlineHRPath = args.HR_Flowline
    outfilepath = Parameters.geonetResultsDir
    inputfilepath = Parameters.demDataFilePath
    demName = Parameters.demFileName
    skel_filename = demName.split('.')[0] + '_flowskeleton.tif'
    thresholdCurvatureQQxx = 1.5
#     outlets = [[2, 4, 9], [27, 26, 23]]
    
    # Read in High Resolution Flowline as GeoPandas DataFrame
    flowline_hr_shp = gpd.read_file(flowlineHRPath)
    # Assign some arbitrary value to the geodataframe where the flowline_hr occurs
    flowline_hr_shp['value'] = 1 # Arbitrary number
    # Subset the dataframe to just the geometry and value columns
    flowline_hr_shp = flowline_hr_shp[['geometry','value']]
    flowline_hr_shp.columns
    # Buffer the flowline
    flowline_hr_shp['geometry'] = flowline_hr_shp.geometry.buffer(5)
    skel_fp = os.path.join(outfilepath,skel_filename)
    skel_raster = rasterio.open(skel_fp)
    meta = skel_raster.meta.copy()
    meta.update(compress='lzw')
    filteredDemArray = read_geotif_filteredDEM()
    with rasterio.open(skel_fp, 'w+', **meta) as out:
        out_arr = out.read(1)
        shapes = ((geom,val) for geom,val in zip(flowline_hr_shp.geometry,flowline_hr_shp.value))
        flowline_hr_raster = features.rasterize(shapes=shapes,fill=1,out=out_arr,transform=out.transform)


    del flowline_hr_shp
    flowline_hr_raster = flowline_hr_raster.astype(np.uint8)
    print(flowline_hr_raster.dtype)
    # Write out High Resolution flowlines
    outfilename = demName.split('.')[0] + '_NHD_HR.tif'
    write_geotif_skeleton(flowline_hr_raster,
                         outfilepath,outfilename)
    del flowline_hr_raster

        
if __name__ == '__main__':
    t0 = perf_counter()
    main()
    t1 = perf_counter()
    print(("time taken to complete skeleton definition:", t1-t0, " seconds"))

