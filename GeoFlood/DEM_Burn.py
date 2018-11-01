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
    

def array2raster(newRasterfn,rasterfn,array,datatype,NoData_value):
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
    outband.SetNoDataValue(NoData_value)
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
    #DEM_name = "DEM"
    geofloodInputDir = os.path.join(geofloodHomeDir, "Inputs",
                                    "GIS", projectName)
    geofloodResultsDir = os.path.join(geofloodHomeDir, "Outputs",
                                      "GIS", projectName)
    demfn = os.path.join(geofloodInputDir, DEM_name+".tif")
    Name_path = os.path.join(geofloodResultsDir, DEM_name)
    pathfn = Name_path + '_path.tif'
    burnpathfn = Name_path + '_burn.tif'
    demArray = raster2array(demfn)
    pathArray = raster2array(pathfn)
    raster = gdal.Open(demfn)
    band = raster.GetRasterBand(1)
    NoData_value = band.GetNoDataValue()
    print NoData_value
    burnArray = np.copy(demArray)
    burnArray = np.where(pathArray == 1, burnArray-100, burnArray)
    burnArray = np.where(np.isnan(demArray), np.nan, burnArray)
    array2raster(burnpathfn, demfn, burnArray,gdal.GDT_Float32,NoData_value)
    

if __name__ == '__main__':
    main()
                

    
        
        
