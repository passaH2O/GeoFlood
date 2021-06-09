from __future__ import division
import os
import pandas as pd
from osgeo import ogr, gdal, osr
import configparser
import inspect
from time import perf_counter 
from GeoFlood_Filename_Finder import cfg_finder


def network_mapping(cat_shp, seg_shp, map_csv):
    shapefile = seg_shp
    driver = ogr.GetDriverByName("ESRI Shapefile")
    dataSource = driver.Open(seg_shp, 0)
    layer = dataSource.GetLayer()
    hydroid_list = []
    comid_list = []
    for feature in layer:
        geom = feature.GetGeometryRef()
        pnt = geom.Centroid()
        cat_Source = driver.Open(cat_shp, 0)
        cat_layer = cat_Source.GetLayer()
        for cat_feat in cat_layer:
            if pnt.Intersects(cat_feat.GetGeometryRef()):
                hydroid = feature.GetField("HYDROID")
                comid = cat_feat.GetField("FEATUREID")
                hydroid_list.append(hydroid)
                comid_list.append(comid)
    df = pd.DataFrame({"HYDROID" : hydroid_list, "COMID" : comid_list})
    print(len(df))
    df.to_csv(map_csv, index=False, columns=['HYDROID', 'COMID'])


def main():
    geofloodHomeDir,projectName,DEM_name,chunk_status,input_fn,output_fn,hr_status = cfg_finder()
    geofloodInputDir = os.path.join(geofloodHomeDir, input_fn,
                                    "GIS", projectName) 
    cat_shp = os.path.join(geofloodInputDir, "Catchment.shp")
    geofloodResultsDir = os.path.join(geofloodHomeDir, output_fn,
                                      "GIS", projectName)
    Name_path = os.path.join(geofloodResultsDir, DEM_name)
    seg_shp = Name_path + "_channelSegment.shp"
    map_csv = Name_path + "_networkMapping.csv"
    network_mapping(cat_shp, seg_shp, map_csv)


if __name__ == '__main__':
    t0 = perf_counter()
    main()
    t1 = perf_counter()
    print(("time taken to map network:", t1-t0, " seconds"))
