from __future__ import division
import os
import numpy as np
from scipy import stats
from osgeo import gdal,ogr
import configparser
import inspect
from time import perf_counter 
from GeoFlood_Filename_Finder import cfg_finder


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
    cat_layer.CreateField(ogr.FieldDefn('AreaSqKm', ogr.OFTReal))
    for feat in cat_layer:
        geom = feat.GetGeometryRef()
        feat.SetField('AreaSqKm',float(geom.Area())/1000**2)
        cat_layer.SetFeature(feat)
        feat.Destroy()
    

    # Initialize Counter for the for loop iterations
    ac_iter = 0

    # Initialize lists to hold each iterations z and m values. Each loop will append to the list.
    z_array_dummy = []
    m_array_dummy = []
    slope_array_dummy = []
    neg_slope_count = []

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
        px = ((mx - gt[0]) / gt[1]).astype(int)
        py = ((my - gt[3]) / gt[5]).astype(int)
        x_diff = np.diff(px)
        y_diff = np.diff(py)
        m_array = np.sqrt(x_diff**2 + y_diff**2)
        m_array = np.insert(m_array, 0, 0)
        m_array = np.cumsum(m_array)

        z_array = rasterBand.ReadAsArray()[py, px].flatten()

        # Gets rid of geometries that are empty
        if np.sum(m_array) == 0:
            print('Empty Geometry Encountered')
            continue
 
        # Append the current iteration to the dummy/container array.
        m_array_dummy.append(m_array)
        # Convert to a numpy array of arrays instead of a list of arrays. This allows it to be indexed numerically.
        m_array_dummy_np = np.asarray(m_array_dummy) 

        # Same instructions used for the 'm_array_dummy' variable are done in the follwing two lines for z.
        z_array_dummy.append(z_array)
        z_array_dummy_np = np.asarray(z_array_dummy)

        slope = -stats.linregress(m_array, z_array)[0]

        if slope < 0:
            neg_slope_count.append(1)
        
        # As done with the m and z values, append each new slope iteration to the 'slope_array_dummy' array 
        # and convert it to a numpy array. This will be used for indexing slope values.

        slope_array_dummy.append(slope)
        slope_array_dummy_np = np.asarray(slope_array_dummy)
        
        
        ###### Correcting Negative and Hydroflattened Slopes: Cycles through previous reaches until the regression slope is positive.
        ###### A value of 0.000001 was chosen as the cut off as not all hydroflattened reaches have a slope of exactly zero, i.e. 9x10^-9. 
        ###### As a result, any value below the threshold chosen will recompute the regression line with its upstream reaches until the 
        ###### slope becomes positive or there are no more reaches to cycle through. If the latter occurs, a slope of 0.00001 is assigned.

        subtraction_iter = 1
        while slope <= 0.000001 and ac_iter>0:
            
            # Append upstream segments to the beginning of the array until the slope from the regression equation is positive.
            # The subtraction_iter term increases with every iteration, so the dummy array's will be sliced from that
            # new array (an older entry) to the current array (the last entry in the array).

                    
            previous_reach_index = ac_iter - subtraction_iter
            z_array_test = np.concatenate(z_array_dummy_np[previous_reach_index:])
            m_array_test = np.concatenate(m_array_dummy_np[previous_reach_index:])
            
            # Linear regression with the appended m and z arrays.
            slope = -stats.linregress(m_array_test, z_array_test)[0]
                       
            # If the number of reaches it is trying to slice is greater than what is contained in the array, assign the slope
            # a small, positive number.
            if subtraction_iter > ac_iter:
                slope = .000001
            subtraction_iter += 1

        cat_layer.SetAttributeFilter("HYDROID = "+str(feat_id))
        area = 0
        for feat in cat_layer:
            area += feat.GetField("AreaSqKm")
            feat.Destroy()
        feature.Destroy()
        rafile.write(str(feat_id)+" "+str(slope)+" "+str(length)+" "+str(area)+"\n")
        ac_iter += 1
    print(f'Total Initial Negative Slopes: {len(neg_slope_count)}')
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
    demfn = os.path.join(geofloodHomeDir, input_fn,
                         "GIS", projectName, DEM_name+".tif")
    river_attribute_estimation(segment_shp, segcatfn,segcat_shp, demfn,attribute_txt)


if __name__ == '__main__':
    t0 = perf_counter()
    main()
    t1 = perf_counter()
    print(("time taken to estimate river attributes:", t1-t0, " seconds"))
