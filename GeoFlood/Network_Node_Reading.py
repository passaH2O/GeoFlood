from __future__ import division
from osgeo import ogr
import os
import pandas as pd
import configparser
import inspect
from time import perf_counter 


def network_node_reading(in_shp, node_csv):

    driver = ogr.GetDriverByName("ESRI Shapefile")
    dataSource = driver.Open(in_shp, 0)
    layer = dataSource.GetLayer()
    start_x_list = []
    start_y_list = []
    from_node_list = []
    to_node_list = []
    first_point_list = []
    last_point_list = []
    for feature in layer:
        geom = feature.GetGeometryRef()
        firstpoint = geom.GetPoint(0)
        lastpoint = geom.GetPoint(geom.GetPointCount()-1)
        from_node_list.append(feature.GetField("FromNode"))
        to_node_list.append(feature.GetField("ToNode"))
        first_point_list.append(firstpoint)
        last_point_list.append(lastpoint)
##        if feature.GetField("StreamOrde") == 1:
##            firstpoint = geom.GetPoint(0)
##            start_x_list.append(firstpoint[0])
##            start_y_list.append(firstpoint[1])
    for i in range(len(from_node_list)):
        if from_node_list[i] not in to_node_list:
            start_x_list.append(first_point_list[i][0])
            start_y_list.append(first_point_list[i][1])
    for i in range(len(to_node_list)):
        if to_node_list[i] not in from_node_list:
            end_x_list = [last_point_list[i][0]]*len(start_x_list)
            end_y_list = [last_point_list[i][1]]*len(start_x_list)
    df = pd.DataFrame({"RiverID": list(range(1, len(start_x_list)+1)),
                       "START_X": start_x_list,
                       "START_Y": start_y_list,
                       "END_X": end_x_list,
                       "END_Y": end_y_list})
    df = df[["RiverID", "START_X", "START_Y", "END_X", "END_Y"]]
    df.to_csv(node_csv, index=False)


def main():
    config = configparser.RawConfigParser()
    config.read(os.path.join(os.path.dirname(
        os.path.dirname(
            inspect.stack()[0][1])),
                             'GeoFlood.cfg'))
    geofloodHomeDir = config.get('Section', 'geofloodhomedir')
    projectName = config.get('Section', 'projectname')
    DEM_name = config.get('Section', 'dem_name')
    geofloodInputDir = os.path.join(geofloodHomeDir, "Inputs",
                                    "GIS", projectName) 
    flowline_shp = os.path.join(geofloodInputDir, "Flowline.shp")
    geofloodResultsDir = os.path.join(geofloodHomeDir, "Outputs",
                                      "GIS", projectName)
    Name_path = os.path.join(geofloodResultsDir, DEM_name)
    node_csv = Name_path + '_endPoints.csv'
    network_node_reading(flowline_shp, node_csv)


if __name__ == '__main__':
    t0 = perf_counter()
    main()
    t1 = perf_counter()
    print(("time taken to detect end points:", t1-t0, " seconds"))
