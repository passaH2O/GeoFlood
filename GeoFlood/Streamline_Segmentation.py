from __future__ import division
import os
import math
from osgeo import ogr
import gdal, osr
import configparser
import inspect
import geopandas as gpd
from time import perf_counter
from GeoFlood_Filename_Finder import cfg_finder

def _distance(a, b):
    dx = abs(b[0] - a[0])
    dy = abs(b[1] - a[1])
    return (dx ** 2 + dy ** 2) ** 0.5


def split_line_single(line, length):
    line_points = line.GetPoints()
    sub_line = ogr.Geometry(ogr.wkbLineString)
    while length > 0:
        d = _distance(line_points[0], line_points[1])
        if d >= length:
            sub_line.AddPoint(*line_points[0])
            sub_line.AddPoint(*line_points[1])
            line_points.remove(line_points[0])
            break
        if d < length:
            sub_line.AddPoint(*line_points[0])
            line_points.remove(line_points[0])
            length -= d
    remainder = ogr.Geometry(ogr.wkbLineString)
    for point in line_points:
        remainder.AddPoint(*point)
    return sub_line, remainder


def network_split(in_shp, out_shp, split_distance):
    driver = ogr.GetDriverByName("ESRI Shapefile")
    dataSource = driver.Open(in_shp, 0)
    layer = dataSource.GetLayer()
    srs = layer.GetSpatialRef()
    ds = driver.CreateDataSource(out_shp)
    output_layer = ds.CreateLayer(out_shp,
                                  srs, ogr.wkbLineString)
    output_layer.CreateField(ogr.FieldDefn("HYDROID", ogr.OFTInteger))
    output_layer.CreateField(ogr.FieldDefn("Length", ogr.OFTReal))
    HydroID = 1
    for feature in layer:
        line = feature.GetGeometryRef()
        no_segments = int(math.ceil(line.Length() / split_distance))
        if no_segments == 0:
            remainder = line
            feat = ogr.Feature(output_layer.GetLayerDefn())
            feat.SetGeometry(remainder)
            feat.SetField('HYDROID', HydroID)
            feat.SetField('Length',remainder.Length())
            HydroID += 1
            output_layer.CreateFeature(feat)
            feat.Destroy()
        else:
            length = line.Length()/no_segments
            remainder = line
            for i in range(no_segments-1):
                segment, remainder = split_line_single(remainder, length)
                feat = ogr.Feature(output_layer.GetLayerDefn())
                feat.SetGeometry(segment)
                feat.SetField('HYDROID', HydroID)
                feat.SetField('Length',segment.Length())
                HydroID += 1
                output_layer.CreateFeature(feat)
                feat.Destroy()
            feat = ogr.Feature(output_layer.GetLayerDefn())
            feat.SetGeometry(remainder)
            feat.SetField('HYDROID', HydroID)
            feat.SetField('Length',remainder.Length())
            HydroID += 1
            output_layer.CreateFeature(feat)
            feat.Destroy()
    ds.Destroy()


def main():
    geofloodHomeDir,projectName,DEM_name,chunk_status,input_fn,output_fn,hr_status = cfg_finder()
    geofloodResultsDir = os.path.join(geofloodHomeDir, output_fn,
                                     "GIS", projectName)
    Name_path = os.path.join(geofloodResultsDir, DEM_name)
    in_shp = Name_path+ "_channelNetwork.shp"
    out_shp = Name_path+ "_channelSegment.shp"
    split_distance = 1000
    network_split(in_shp, out_shp, split_distance)


if __name__ == '__main__':
    t0 = perf_counter()
    main()
    t1 = perf_counter()
    print(("time taken to segment streamline:", t1-t0, " seconds"))
