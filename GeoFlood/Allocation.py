import os
import gdal, osr
from osgeo import ogr
import numpy as np


global d_x = [-1,-1,0,1,1,1,0,-1]
global d_y = [0,-1,-1,-1,0,1,1,1]
global g_x = [1.0,1.0,0.0,1.0,1.0,1.0,0.0,1.0]
global g_y = [0.0,1.0,1.0,1.0,0.0,1.0,1.0,1.0]


def raster2array(rasterfn):
    raster = gdal.Open(rasterfn)
    band = raster.GetRasterBand(1)
    array = band.ReadAsArray()
    return array


def euclidean_allocation(demArray, pathArray):
    global d_x, d_y, g_x, g_y
    distanceArray = np.full(demArray, nodata)
    allocationArray = np.zeros_like(demArray)
    distanceArray = np.where(pathArray == 1, 0, np.inf)
    allocationArray = np.where(pathArray == 1, demArray, np.inf)
    nodata = -9999
    r_x = np.full(demArray, nodata)
    r_y = np.full(demArray, nodata)
    for row in range(distanceArray.shape[0]):
        for col in range(distanceArray.shape[1]):
            z = distanceArray[row, col]
            if z != 0:
                z_min = np.inf
                which_cell = 0
                for i in range(4):
                    x = col + d_x[i]
                    y = row + d_y[i]
                    z2 = distanceArray[y,x]
                    if z2 != nodata:
                        if i == 0:
                            h = 2*r_x[y,x]+1
                        elif i == 1:
                            h = 2*(r_x[y,x]+r_y[y,x]+1)
                        elif i == 2:
                            h = 2*r_y[y,x]+1
                        elif i == 3:
                            h = 2*(r_x[y,x]+r_y[y,x]+1)
                        z2 += h
                        if z2 < z_min:
                            z_min = z2
                            which_cell = i
                if z_min < z:
                    distanceArray[row,col] = z_min
                    x = col + d_x[which_cell]
                    y = row + d_y[which_cell]
                    r_x[row, col] = r_x[y,x] + g_x[which_cell]
                    r_y[row, col] = r_y[y,x] + g_y[which_cell]
                    allocationArray[row, col] = allocationArray[y,x]
    for row in range(0,distanceArray.shape[0],-1):
        for col in range(0,distanceArray.shape[1],-1):
            z = distanceArray[row, col]
            if z != 0:
                z_min = np.inf
                which_cell = 0
                for i in range(4,8):
                    x = col + d_x[i]
                    y = row + d_y[i]
                    z2 = distanceArray[y,x]
                    if z2 != nodata:
                        if i == 4:
                            h = 2*r_x[y,x]+1
                        elif i == 5:
                            h = 2*(r_x[y,x]+r_y[y,x]+1)
                        elif i == 6:
                            h = 2*r_y[y,x]+1
                        elif i == 7:
                            h = 2*(r_x[y,x]+r_y[y,x]+1)
                        z2 += h
                        if z2 < z_min:
                            z_min = z2
                            which_cell = i
                if z_min < z:
                    distanceArray[row,col] = z_min
                    x = col + d_x[which_cell]
                    y = row + d_y[which_cell]
                    r_x[row, col] = r_x[y,x] + g_x[which_cell]
                    r_y[row, col] = r_y[y,x] + g_y[which_cell]
                    allocationArray[row, col] = allocationArray[y,x]
    allocationArray = np.where[demArray<0,nodata,allocationArray]
    return allocationArray


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
    outRasterSRS = osr.SpatialReference()
    outRasterSRS.ImportFromWkt(raster.GetProjectionRef())
    outRaster.SetProjection(outRasterSRS.ExportToWkt())
    outband.FlushCache()


def main():

    demfn = "DEM.tif"
    pathfn = "Path.tif"
    allofn = "Allocation.tif"
    demArray = raster2array(demfn)
    pathArray = raster2array(pathfn)
    allocationArray = euclidean_allocation(demArray, pathArray)
    array2raster(allofn,demfn,allocationArray,gdal.GDT_Float32)
    

if __name__ == "__main__":
    main()
