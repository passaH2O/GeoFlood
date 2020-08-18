from __future__ import division
import os
import numpy as np
from scipy import stats
from osgeo import gdal,ogr
import configparser
import inspect
import sys
import pandas as pd

from GeoFlood_Filename_Finder import cfg_finder
from time import perf_counter 
from scipy.stats import gmean,theilslopes

def river_attribute_estimation(segment_shp, segcatfn,
                               segcat_shp, burndemfn,
                               attribute_txt):
    rafile = open(attribute_txt,"w")
    driver = ogr.GetDriverByName("ESRI Shapefile")
    dataSource = driver.Open(segment_shp, 0)
    layer = dataSource.GetLayer()
    srs = layer.GetSpatialRef()
    featureCount = layer.GetFeatureCount()
    rafile.write(str(featureCount)+"\n")
    raster = gdal.Open(burndemfn) 
    gt = raster.GetGeoTransform()
    rasterBand = raster.GetRasterBand(1)
    cat_raster = gdal.Open(segcatfn) 
    cat_rasterBand = cat_raster.GetRasterBand(1)
##    raster_arr = np.array(cat_rasterBand.ReadAsArray())
##    nodata = -32768
##    nodatamask = raster_arr == nodata
##    mask = cat_rasterBand.GetMaskBand().ReadAsArray()
    mask = cat_rasterBand.GetMaskBand()
    ds = driver.CreateDataSource(segcat_shp)
    cat_layer = ds.CreateLayer(segcat_shp, srs)
    field = ogr.FieldDefn("HYDROID", ogr.OFTInteger)
    cat_layer.CreateField(field)
    dst_field = cat_layer.GetLayerDefn().GetFieldIndex("HYDROID")
    gdal.Polygonize(cat_rasterBand, mask, cat_layer, dst_field,
                    [], callback=None)
    ds.Destroy()
    ds = driver.Open(segcat_shp, 1)
    cat_layer = ds.GetLayer()
    schema=[]
    ldefn=cat_layer.GetLayerDefn()
    for n in range(ldefn.GetFieldCount()):
        fdefn = ldefn.GetFieldDefn(n)
        schema.append(fdefn.name)
    cat_layer.CreateField(ogr.FieldDefn('AreaSqKm', ogr.OFTReal))
    new_counter = 0
    for feat in cat_layer:
        geom = feat.GetGeometryRef()
        feat.SetField('AreaSqKm',float(geom.Area())/1000**2)
        cat_layer.SetFeature(feat)
        feat.Destroy()
        new_counter+=1
    

    # Initialize Counter for the for loop iterations
    ac_iter = 0

    # Initialize lists to hold each iterations z and m values. Each loop will append to the list.
    z_array_du = []
    m_array_du = []
    slope_array_du = []
    alec_int = 0
    mx_first=[]
    mx_last=[]
    temp_slope_list = []
    feature_id_list=[]
    print(f'Total Segments: {len(layer)}')
    for feature in layer:
        geom = feature.GetGeometryRef()
        feat_id = feature.GetField('HYDROID')
        length = feature.GetField('Length')/1000
        point_geom_list = geom.GetPoints()
        mx = np.array([])
        my = np.array([])
        for i in range(len(point_geom_list)):
            mx = np.append(mx, point_geom_list[i][0])
            my = np.append(my, point_geom_list[i][1])
        mx_first.append(mx[0]) # Used to check if previous stream is actually upstream from current one
        mx_last.append(mx[-1])
        px = ((mx - gt[0]) / gt[1]).astype(int)
        py = ((my - gt[3]) / gt[5]).astype(int)
        x_diff = np.diff(px)*gt[1]
        y_diff = np.diff(py)*gt[1]
        m_array = np.sqrt(x_diff**2 + y_diff**2)
        m_array = np.insert(m_array, 0, 0)
        m_array = np.cumsum(m_array)
        z_array = rasterBand.ReadAsArray()[py, px].flatten()
        # Gets rid of geometries that are empty
        if np.sum(m_array) == 0:
            print('Empty Geometry Encountered')
            continue

        L_10 = int(len(m_array)*.1)
        L_85 = int(len(m_array)*.85)
        slope = (z_array[L_10]-z_array[L_85])/((m_array[L_85]-m_array[L_10]))
        temp_slope_list.append(slope)

        # Append the current iteration to the du/container array.
        m_array_du.append(m_array)
        # Convert to a numpy array of arrays instead of a list of arrays. This allows it to be indexed numerically.
        m_array_du_np = np.asarray(m_array_du) 

        # Same instructions used for the 'm_array_du' variable are done in the follwing two lines for z.
        z_array_du.append(z_array)
        z_array_du_np = np.asarray(z_array_du)
        
        #########################################################################################################
        # As done with the m and z values, append each new slope iteration to the 'slope_array_du' array 
        # and convert it to a numpy array. This will be used for indexing slope values.

        slope_array_du.append(slope)
        slope_array_du_np = np.asarray(slope_array_du)
        
        ###### Correcting Negative and Hydroflattened Slopes: Cycles through previous reaches until the regression slope is positive.
        ###### A value of 0.000001 was chosen as the cut off as not all hydroflattened reaches have a slope of exactly zero, i.e. 9x10^-9. 
        ###### As a result, any value below the threshold chosen will recompute the regression line with its upstream reaches until the 
        ###### slope becomes positive or there are no more reaches to cycle through. If the latter occurs, a slope of 0.00001 is assigned.

        if (slope<=0.0000001) and (ac_iter==0):
           slope=.00001

        subtraction_iter = 1
        a1_count=0
        prev_check=0
        gmean_check=0
        if (slope<=0.0) and (ac_iter>=1):
            previous_reach_index=ac_iter-subtraction_iter # Just for indexing purposes
            while (slope <= 0.000001) and (mx_first[ac_iter]==mx_last[previous_reach_index]) and (subtraction_iter<=3):
            
                previous_reach_index = ac_iter - subtraction_iter
                prior_length=[]
                prior_array_length=[]
                for i in range(subtraction_iter):
                    prior_length.append(m_array_du_np[previous_reach_index+i][-1])
                    prior_array_length.append(np.size(m_array_du_np[previous_reach_index+i]))

                z_array_test = np.concatenate(z_array_du_np[previous_reach_index:])
                m_array_test = np.concatenate(m_array_du_np[previous_reach_index:])
                for i in range(len(prior_length)):
                    if len(prior_length)<2:
                        m_array_test[prior_array_length[i]:]=m_array_test[prior_array_length[i]:]+prior_length
                    else:
                        if (i+1)<len(prior_length):
                            m_array_test[prior_array_length[i+1]:(prior_array_length[i]+prior_array_length[i+1])]=m_array_test[prior_array_length[i+1]:(prior_array_length[i]+prior_array_length[i+1])]+prior_length[i+1]

                        else:
                            m_array_test[np.sum(prior_array_length):]=m_array_test[np.sum(prior_array_length):]+prior_length[0]
                L_negative_10 = int(np.size(m_array_test)*.1)
                L_negative_85 = int(np.size(m_array_test)*.85)
                slope = (z_array_test[L_negative_10]-z_array_test[L_negative_85])/(m_array_test[L_negative_85]-m_array_test[L_negative_10])
                if (slope>0):
                    prev_check=1
                subtraction_iter+=1
            if (slope<=.000001) and (subtraction_iter>3):
                slope = gmean(slope_array_du_np[slope_array_du_np>0])
                gmean_check=1
        if slope>0.0:
            slope_array_du.append(slope)
        else:
            slope = gmean(slope_array_du_np[slope_array_du_np>0])
            slope_array_du.append(slope)
        alec_int += 1
        cat_layer.SetAttributeFilter("HYDROID = "+str(feat_id))
        area = 0
        for feat in cat_layer:
            area += feat.GetField("AreaSqKm")
            feat.Destroy()
        feature.Destroy()
        rafile.write(str(feat_id)+" "+str(slope)+" "+str(length)+" "+str(area)+"\n")
        ac_iter += 1
        print(f'Segment: {ac_iter}')
        feature_id_list.append(feat_id)
        
    rafile.close()
    dataSource.Destroy()
    ds.Destroy()

def main():
    geofloodHomeDir,projectName,DEM_name,chunk_status,input_fn,output_fn,hr_status = cfg_finder()
    geofloodResultsDir = os.path.join(geofloodHomeDir, output_fn,
                                      "GIS", projectName)
    Name_path = os.path.join(geofloodResultsDir, DEM_name)
    segment_shp = Name_path + "_channelSegment.shp"
    segcatfn = Name_path + "_segmentCatchment.tif"
    segcat_shp = Name_path + "_segmentCatchment.shp"
    hydro_folder = os.path.join(geofloodHomeDir,
                                output_fn, "Hydraulics",
                                projectName)
    if not os.path.exists(hydro_folder):
        os.mkdir(hydro_folder)
    attribute_txt = os.path.join(hydro_folder,
                                 DEM_name+"_River_Attribute.txt")
    demfn = os.path.join(geofloodHomeDir, input_fn,"GIS", projectName, DEM_name+".tif")
    river_attribute_estimation(segment_shp, segcatfn,
                                   segcat_shp, demfn,
                                   attribute_txt)

if __name__ == '__main__':
    t0 = perf_counter()
    main()
    t1 = perf_counter()
    print(("time taken to estimate river attributes:", t1-t0, " seconds"))
