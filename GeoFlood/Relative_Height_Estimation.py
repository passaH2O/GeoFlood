import os
import gdal, osr
from osgeo import ogr
import numpy as np
import ConfigParser
import inspect


global d_x, d_y, g_x, g_y, nodata
d_x = [-1,-1,0,1,1,1,0,-1]
d_y = [0,-1,-1,-1,0,1,1,1]
g_x = [1.0,1.0,0.0,1.0,1.0,1.0,0.0,1.0]
g_y = [0.0,1.0,1.0,1.0,0.0,1.0,1.0,1.0]


def vector2raster(vectorfn, rasterfn, newRasterfn):
    source_ds = ogr.Open(vectorfn)
    source_layer = source_ds.GetLayer()
    raster = gdal.Open(rasterfn)
    geotransform = raster.GetGeoTransform()
    originX = geotransform[0]
    originY = geotransform[3]
    pixelWidth = geotransform[1]
    pixelHeight = geotransform[5]
    band = raster.GetRasterBand(1)
    array = band.ReadAsArray()
    cols = array.shape[1]
    rows = array.shape[0]
    driver = gdal.GetDriverByName('GTiff')
    outRaster = driver.Create(newRasterfn, cols, rows, 1, gdal.GDT_Byte)
    outRaster.SetGeoTransform((originX, pixelWidth, 0, originY, 0, pixelHeight))
    outband = outRaster.GetRasterBand(1)
    gdal.RasterizeLayer(outRaster, [1], source_layer, burn_values=[1])


def getnodata(rasterfn):
    global nodata
    raster = gdal.Open(rasterfn)
    band = raster.GetRasterBand(1)
    nodata = band.GetNoDataValue()
    

def raster2array(rasterfn):
    raster = gdal.Open(rasterfn)
    band = raster.GetRasterBand(1)
    array = band.ReadAsArray()
    return array


def negative_height_identification(demArray, pathArray):
    # Euclidean Allocation
    global d_x, d_y, g_x, g_y
    nodata = -9999
    distanceArray = np.full_like(demArray, nodata)
    allocationArray = np.zeros_like(demArray)
    distanceArray = np.where(pathArray == 1, 0, np.inf)
    allocationArray = np.where(pathArray == 1, demArray, np.inf)
##    r_x = np.full_like(demArray, nodata)
##    r_y = np.full_like(demArray, nodata)
    for row in range(distanceArray.shape[0]):
        for col in range(distanceArray.shape[1]):
            z = distanceArray[row, col]
            if z != 0:
                z_min = np.inf
                which_cell = 0
                for i in range(4):
                    x = col + d_x[i]
                    y = row + d_y[i]
                    if (x >= 0) and (x < distanceArray.shape[1]) and \
                       (y >= 0) and (y < distanceArray.shape[0]):
                        z2 = distanceArray[y,x]
                        if z2 != nodata:
                            if i == 0:
                                h = 1
                                #h = 2*r_x[y,x]+1
                            elif i == 1:
                                h = 1.414
                                #h = 2*(r_x[y,x]+r_y[y,x]+1)
                            elif i == 2:
                                h = 1
                                #h = 2*r_y[y,x]+1
                            elif i == 3:
                                h = 1.411
                                #h = 2*(r_x[y,x]+r_y[y,x]+1)
                            z2 += h
                            if z2 < z_min:
                                z_min = z2
                                which_cell = i
                if z_min < z:
                    distanceArray[row,col] = z_min
                    x = col + d_x[which_cell]
                    y = row + d_y[which_cell]
                    #r_x[row, col] = r_x[y,x] + g_x[which_cell]
                    #r_y[row, col] = r_y[y,x] + g_y[which_cell]
                    allocationArray[row, col] = allocationArray[y,x]
    for row in range(distanceArray.shape[0]-1,-1,-1):
        for col in range(distanceArray.shape[1]-1,-1,-1):
            z = distanceArray[row, col]
            if z != 0:
                z_min = np.inf
                which_cell = 0
                for i in range(4,8):
                    x = col + d_x[i]
                    y = row + d_y[i]
                    if (x >= 0) and (x < distanceArray.shape[1]) and \
                       (y >= 0) and (y < distanceArray.shape[0]):
                        z2 = distanceArray[y,x]
                        if z2 != nodata:
                            if i == 4:
                                h = 1
                                #h = 2*r_x[y,x]+1
                            elif i == 5:
                                h = 1.414
                                #h = 2*(r_x[y,x]+r_y[y,x]+1)
                            elif i == 6:
                                h = 1
                                #h = 2*r_y[y,x]+1
                            elif i == 7:
                                h = 1.414
                                #h = 2*(r_x[y,x]+r_y[y,x]+1)
                            z2 += h
                            if z2 < z_min:
                                z_min = z2
                                which_cell = i
                if z_min < z:
                    distanceArray[row,col] = z_min
                    x = col + d_x[which_cell]
                    y = row + d_y[which_cell]
                    #r_x[row, col] = r_x[y,x] + g_x[which_cell]
                    #r_y[row, col] = r_y[y,x] + g_y[which_cell]
                    allocationArray[row, col] = allocationArray[y,x]
    allocationArray = np.where(demArray==nodata,nodata,allocationArray)
    allocationArray = np.where(np.isinf(allocationArray),nodata,allocationArray)
    relaHeightArray = np.where(allocationArray<demArray,0,1)
    return allocationArray, relaHeightArray


def array2raster(newRasterfn,rasterfn,array,datatype):
    global nodata
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
    outband.SetNoDataValue(nodata)
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
    geofloodInputDir = os.path.join(geofloodHomeDir, "Inputs",
                                    "GIS", projectName) 
    flowline_shp = os.path.join(geofloodInputDir, "Flowline.shp")
    demfn = os.path.join(geofloodInputDir, DEM_name+".tif")
    geofloodResultsDir = os.path.join(geofloodHomeDir, "Outputs",
                                      "GIS", projectName)
    Name_path = os.path.join(geofloodResultsDir, DEM_name)
    nhdfn = Name_path + '_nhdflowline.tif'
    allofn = Name_path + '_Allocation.tif'
    negahandfn = Name_path + "_NegaHand.tif"
    demArray = raster2array(demfn)
    getnodata(demfn)
    vector2raster(flowline_shp, demfn, nhdfn)
    pathArray = raster2array(nhdfn)
    allocationArray, relaHeightArray = negative_height_identification(demArray, pathArray)
    array2raster(allofn,demfn,allocationArray,gdal.GDT_Float32)
    array2raster(negahandfn,demfn,relaHeightArray,gdal.GDT_Byte)
    

if __name__ == "__main__":
    main()
