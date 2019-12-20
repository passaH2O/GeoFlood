# PyGeoNet functions for raster I/O
import os
import sys
import numpy as np
from osgeo import gdal
from osgeo import osr
from osgeo import ogr
import pygeonet_prepare as Parameters
import pygeonet_defaults as defaults


# Read dem information
def read_dem_from_geotiff(demFileName, demFilePath):
    # Open the GeoTIFF format DEM
    fullFilePath = os.path.join(demFilePath, demFileName)
    print(('reading geotiff', demFileName))
    # Use GDAL functions to read the dem as a numpy array
    # and get the dem extent, resolution, and projection
    ary = []
    gdal.UseExceptions()
    ds = gdal.Open(fullFilePath, gdal.GA_ReadOnly)
    driver = ds.GetDriver()
    geotransform = ds.GetGeoTransform()
    Parameters.geotransform = geotransform
    ary = ds.GetRasterBand(1).ReadAsArray()
    Parameters.demPixelScale = float(geotransform[1])
    Parameters.xLowerLeftCoord = float(geotransform[0])
    Parameters.yLowerLeftCoord = float(geotransform[3])
    Parameters.inputwktInfo = ds.GetProjection()
    # return the dem as a numpy array
    return ary


# Read geotif from file on a disk
def read_geotif_filteredDEM():
    intif = Parameters.pmGrassGISfileName
    ds = gdal.Open(intif, gdal.GA_ReadOnly)
    driver = ds.GetDriver()
    ary = ds.GetRasterBand(1).ReadAsArray()
    geotransform = ds.GetGeoTransform()
    Parameters.geotransform = geotransform
    Parameters.demPixelScale = float(geotransform[1])
    Parameters.inputwktInfo = ds.GetProjection()
    return ary


# Read geotif from file on a disk
def read_geotif_generic(intifpath, intifname):
    intif = os.path.join(intifpath, intifname)
    ds = gdal.Open(intif, gdal.GA_ReadOnly)
    ary = ds.GetRasterBand(1).ReadAsArray()
    return ary


# Write geotif to file on a disk
def write_geotif_generic(inputArray, outfilepath, outfilename):
    print(('writing geotiff', outfilename))
    output_fileName = os.path.join(outfilepath, outfilename)
    # Get shape
    nrows = inputArray.shape[0]
    ncols = inputArray.shape[1]
    # create the output image
    driver = gdal.GetDriverByName('GTiff')
    outDs = driver.Create(output_fileName, ncols, nrows, 1, gdal.GDT_Float32)
    if outDs is None:
        print(('Could not create ' + outfilename))
        sys.exit(1)
    outBand = outDs.GetRasterBand(1)
    # set the reference info
    geotransform = Parameters.geotransform
    cc = (geotransform[0], geotransform[1], geotransform[2],
          geotransform[3], geotransform[4], geotransform[5])
    outDs.SetGeoTransform(cc)
    outDs.SetProjection(Parameters.inputwktInfo)
    # write the band
    tmparray = np.array(inputArray)
    outBand.WriteArray(tmparray)
    # flush data to disk, set the NoData value and calculate stats
    outBand.FlushCache()
    del tmparray, outDs, outBand, driver


# Write filtered geotiff to disk to be used by GRASS GIS
def write_geotif_filteredDEM(filteredDemArray, filepath, filename):
    print ('writing filtered DEM')
    output_fileName = Parameters.pmGrassGISfileName
    # Create gtif
    nrows = filteredDemArray.shape[0]
    ncols = filteredDemArray.shape[1]
    print(('filtered DEM size:', str(nrows), 'rowsx', str(ncols), 'columns'))
    # create the output image
    driver = gdal.GetDriverByName('GTiff')
    outDs = driver.Create(output_fileName, ncols, nrows, 1, gdal.GDT_Float32)
    if outDs is None:
        print ('Could not create tif file')
        sys.exit(1)
    # set the reference info
    geotransform = Parameters.geotransform
    outDs.SetGeoTransform(geotransform)
    outDs.SetProjection(Parameters.inputwktInfo)
    # write the band
    outband = outDs.GetRasterBand(1)
    outband.WriteArray(filteredDemArray)
    outRasterSRS = osr.SpatialReference(wkt=Parameters.inputwktInfo)
    authoritycode = outRasterSRS.GetAuthorityCode("PROJCS")
    outRasterSRS.ImportFromEPSG(int(authoritycode))
    outDs.SetProjection(outRasterSRS.ExportToWkt())
    outband.FlushCache()
    # finishing the writing of filtered DEM
    del outDs, outband, driver, outRasterSRS
