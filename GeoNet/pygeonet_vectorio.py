import os
import numpy as np
from osgeo import ogr
from osgeo import osr
from osgeo import gdal
import pygeonet_prepare as Parameters


# Writing drainage network node (head/junction) shapefiles
def write_drainage_nodes(xx, yy, node_type, fileName, shapeName):
    print(f'Writing {node_type} shapefile')
    # set up the shapefile driver
    driver = ogr.GetDriverByName(Parameters.driverName)
    # This will delete and assist in overwrite of the shape files
    if os.path.exists(fileName):
        driver.DeleteDataSource(fileName)
    # create the data source
    data_source = driver.CreateDataSource(fileName)
    # create the spatial reference, same as the input dataset
    if not hasattr(Parameters, 'geotransform'):
        fullFilePath = os.path.join(Parameters.demDataFilePath,
                                    Parameters.demFileName)
        ds = gdal.Open(fullFilePath, gdal.GA_ReadOnly)
        geotransform = ds.GetGeoTransform()
        Parameters.geotransform = geotransform
        Parameters.inputwktInfo = ds.GetProjection()
    srs = osr.SpatialReference()
    gtf = Parameters.geotransform
    georef = Parameters.inputwktInfo
    srs.ImportFromWkt(georef)
    # Project the xx, and yy points
    xxProj = (float(gtf[0]) +
              float(gtf[1]) * np.array(xx))
    yyProj = (float(gtf[3]) +
              float(gtf[5]) * np.array(yy))
    # create the layer
    layer = data_source.CreateLayer(shapeName,
                                    srs, ogr.wkbPoint)
    # Add the fields we're interested in
    field_name = ogr.FieldDefn("Type", ogr.OFTString)
    field_name.SetWidth(24)
    layer.CreateField(field_name)
    layer.CreateField(ogr.FieldDefn("Latitude", ogr.OFTReal))
    layer.CreateField(ogr.FieldDefn("Longitude", ogr.OFTReal))
    # Now add the channel heads as features to the layer
    for i in range(0, len(xxProj)):
        # create the feature
        feature = ogr.Feature(layer.GetLayerDefn())
        # Set the attributes using the values
        feature.SetField("Type", node_type)
        feature.SetField("Latitude", xxProj[i])
        feature.SetField("Longitude", yyProj[i])
        # create the WKT for the feature using Python string formatting
        wkt = "POINT(%f %f)" % (float(xxProj[i]), float(yyProj[i]))
        # Create the point from the Well Known Txt
        point = ogr.CreateGeometryFromWkt(wkt)
        # Set the feature geometry using the point
        feature.SetGeometry(point)
        # Create the feature in the layer (shapefile)
        layer.CreateFeature(feature)
        # Destroy the feature to free resources
        feature.Destroy()
    # Destroy the data source to free resources
    data_source.Destroy()


# Writing drainage paths as shapefile
def write_drainage_paths(geodesicPathsCellList):
    print('Writing drainage paths')
    driver = ogr.GetDriverByName(Parameters.driverName)
    if os.path.exists(Parameters.drainagelineFileName):
        driver.DeleteDataSource(Parameters.drainagelineFileName)
    data_source = driver.CreateDataSource(Parameters.drainagelineFileName)
    if not hasattr(Parameters, 'geotransform'):
        fullFilePath = os.path.join(Parameters.demDataFilePath,
                                    Parameters.demFileName)
        ds = gdal.Open(fullFilePath, gdal.GA_ReadOnly)
        geotransform = ds.GetGeoTransform()
        Parameters.geotransform = geotransform
        Parameters.inputwktInfo = ds.GetProjection()
    srs = osr.SpatialReference()
    gtf = Parameters.geotransform
    georef = Parameters.inputwktInfo
    srs.ImportFromWkt(georef)
    layer = data_source.CreateLayer(Parameters.drainagelinefileName,
                                    srs, ogr.wkbLineString)
    field_name = ogr.FieldDefn("Type", ogr.OFTString)
    field_name.SetWidth(24)
    layer.CreateField(field_name)
    for i in range(0, len(geodesicPathsCellList)):
        # Project the linepoints to appropriate projection
        xx = geodesicPathsCellList[i][1]
        yy = geodesicPathsCellList[i][0]
        # Project the xx, and yy points
        xxProj = (float(gtf[0]) +
                  float(gtf[1]) * np.array(xx))
        yyProj = (float(gtf[3]) +
                  float(gtf[5]) * np.array(yy))
        # create the feature
        feature = ogr.Feature(layer.GetLayerDefn())
        # Set the attributes using the values
        feature.SetField("Type", 'ChannelNetwork')
        # create the WKT for the feature using Python string formatting
        line = ogr.Geometry(ogr.wkbLineString)
        for j in xrange(0, len(xxProj)):
            line.AddPoint(xxProj[j], yyProj[j])
        # Create the point from the Well Known Txt
        # lineobject = line.ExportToWkt()
        # Set the feature geometry using the point
        feature.SetGeometryDirectly(line)
        # Create the feature in the layer (shapefile)
        layer.CreateFeature(feature)
        # Destroy the feature to free resources
        feature.Destroy()
    # Destroy the data source to free resources
    data_source.Destroy()


# Writing cross section shapefiles
def write_cross_sections(TotalcrossSectionsXYArray, XSIDArray):
    print("Writing Cross Sections shapefile")
    driver = ogr.GetDriverByName(Parameters.driverName)
    if os.path.exists(Parameters.xsFileName):
        driver.DeleteDataSource(Parameters.xsFileName)
    data_source = driver.CreateDataSource(Parameters.xsFileName)
    if not hasattr(Parameters, 'geotransform'):
        fullFilePath = os.path.join(Parameters.demDataFilePath,
                                    Parameters.demFileName)
        ds = gdal.Open(fullFilePath, gdal.GA_ReadOnly)
        geotransform = ds.GetGeoTransform()
        Parameters.geotransform = geotransform
        Parameters.inputwktInfo = ds.GetProjection()
    srs = osr.SpatialReference()
    gtf = Parameters.geotransform
    georef = Parameters.inputwktInfo
    srs.ImportFromWkt(georef)
    layer = data_source.CreateLayer(Parameters.xsshapefileName,
                                    srs, ogr.wkbLineString)
    field_name = ogr.FieldDefn("Type", ogr.OFTString)
    field_name.SetWidth(24)
    layer.CreateField(field_name)
    layer.CreateField(ogr.FieldDefn("ID", ogr.OFTInteger))
    for i in range(0, len(TotalcrossSectionsXYArray)):
        xx = TotalcrossSectionsXYArray[i][1]
        yy = TotalcrossSectionsXYArray[i][0]
        xxProj = (float(gtf[0]) +
                  float(gtf[1]) * np.array(xx))
        yyProj = (float(gtf[3]) +
                  float(gtf[5]) * np.array(yy))
        feature = ogr.Feature(layer.GetLayerDefn())
        feature.SetField("Type", 'CrossSection')
        feature.SetField("ID", XSIDArray[i])
        line = ogr.Geometry(ogr.wkbLineString)
        for j in xrange(0, len(xxProj)):
            line.AddPoint(xxProj[j], yyProj[j])
        feature.SetGeometryDirectly(line)
        layer.CreateFeature(feature)
        feature.Destroy()
    data_source.Destroy()


# Writing drainage paths as shapefile
def write_bank_lines(leftBankCellList, rightBankCellList):
    print('Writing bank lines')
    driver = ogr.GetDriverByName(Parameters.driverName)
    if os.path.exists(Parameters.banklineFileName):
        driver.DeleteDataSource(Parameters.banklineFileName)
    data_source = driver.CreateDataSource(Parameters.banklineFileName)
    if not hasattr(Parameters, 'geotransform'):
        fullFilePath = os.path.join(Parameters.demDataFilePath,
                                    Parameters.demFileName)
        ds = gdal.Open(fullFilePath, gdal.GA_ReadOnly)
        geotransform = ds.GetGeoTransform()
        Parameters.geotransform = geotransform
        Parameters.inputwktInfo = ds.GetProjection()
    srs = osr.SpatialReference()
    gtf = Parameters.geotransform
    georef = Parameters.inputwktInfo
    srs.ImportFromWkt(georef)
    layer = data_source.CreateLayer(Parameters.banklinefileName,
                                    srs, ogr.wkbLineString)
    field_name = ogr.FieldDefn("Type", ogr.OFTString)
    field_name.SetWidth(24)
    layer.CreateField(field_name)
    field_name = ogr.FieldDefn("Side", ogr.OFTString)
    field_name.SetWidth(24)
    layer.CreateField(field_name)
    for n in range(2):
        if n == 0:
            BankCellList = leftBankCellList
            Bank = 'Left'
        else:
            BankCellList = rightBankCellList
            Bank = 'Right'
        for i in range(0, len(leftBankCellList)):
            xx = BankCellList[i][1]
            yy = BankCellList[i][0]
            xxProj = (float(gtf[0]) +
                      float(gtf[1]) * np.array(xx))
            yyProj = (float(gtf[3]) +
                      float(gtf[5]) * np.array(yy))
            feature = ogr.Feature(layer.GetLayerDefn())
            feature.SetField("Type", "Bank")
            feature.SetField("Type", Bank)
            line = ogr.Geometry(ogr.wkbLineString)
            for j in xrange(0, len(xxProj)):
                line.AddPoint(xxProj[j], yyProj[j])
            feature.SetGeometryDirectly(line)
            layer.CreateFeature(feature)
            feature.Destroy()
    data_source.Destroy()
