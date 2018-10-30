import numpy as np
import os
import gdal, osr
from osgeo import ogr
import ConfigParser
import inspect


def raster2array(rasterfn):
    raster = gdal.Open(rasterfn)
    band = raster.GetRasterBand(1)
    array = band.ReadAsArray()
    return array
    

def array2raster(newRasterfn,rasterfn,array,datatype):
    raster = gdal.Open(rasterfn)
    geotransform = raster.GetGeoTransform()
    originX = geotransform[0]
    originY = geotransform[3]
    pixelWidth = geotransform[1]
    pixelHeight = geotransform[5]
    cols = array.shape[1]
    rows = array.shape[0]
    driver = gdal.GetDriverByName('GTiff')
    outRaster = driver.Create(newRasterfn, cols, rows, 1, datatype)
    outRaster.SetGeoTransform((originX, pixelWidth, 0, originY, 0, pixelHeight))
    outband = outRaster.GetRasterBand(1)
    outband.WriteArray(array)
    outband.SetNoDataValue(-9999)
    outRasterSRS = osr.SpatialReference()
    outRasterSRS.ImportFromWkt(raster.GetProjectionRef())
    outRaster.SetProjection(outRasterSRS.ExportToWkt())
    outband.FlushCache()


def main():
    config = ConfigParser.RawConfigParser()
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
    geofloodResultsDir = os.path.join(geofloodHomeDir, "Outputs",
                                      "GIS", projectName)
    Name_path = os.path.join(geofloodResultsDir, DEM_name)
    pathfn = Name_path + '_path.tif'
    burnfdrfn = Name_path + '_burnp.tif'
    streamfdrfn = Name_path + '_streamp.tif'
    pathArray = raster2array(pathfn)
    burnfdrArray = raster2array(burnfdrfn)
    streamfdrArray = np.where(pathArray == 1, burnfdrArray, -9999)
    array2raster(streamfdrfn, pathfn, streamfdrArray, gdal.GDT_Int16)
    

if __name__ == '__main__':
    main()
                

    
        
        
