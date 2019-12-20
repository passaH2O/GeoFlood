from __future__ import division
import os
import pandas as pd
from osgeo import ogr
import gdal, osr
import configparser
import inspect
from time import perf_counter 



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
    df.to_csv(map_csv, index=False, columns=['HYDROID', 'COMID'])


def main():
    config = configparser.RawConfigParser()
    config.read(os.path.join(os.path.dirname(
        os.path.dirname(
            inspect.stack()[0][1])),
                             'GeoFlood.cfg'))
    geofloodHomeDir = config.get('Section', 'geofloodhomedir')
    projectName = config.get('Section', 'projectname')
    DEM_name = config.get('Section', 'dem_name')
    #geofloodHomeDir = "H:\GeoFlood"
    #projectName = "Test_Stream"
    #DEM_name = "DEM"
    geofloodInputDir = os.path.join(geofloodHomeDir, "Inputs",
                                    "GIS", projectName) 
    cat_shp = os.path.join(geofloodInputDir, "Catchment.shp")
    geofloodResultsDir = os.path.join(geofloodHomeDir, "Outputs",
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
