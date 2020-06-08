from __future__ import division
import os
import gdal, osr
import psutil
import math
import numpy as np
np.seterr(divide='ignore', invalid='ignore')
import pandas as pd
import configparser
import inspect
import gc
import rasterio

from osgeo import ogr
from skimage.graph import route_through_array
from time import perf_counter
from rasterio.mask import mask
from rasterio.windows import Window
from GeoFlood_Filename_Finder import cfg_finder

originX = 0.0
originY = 0.0
pixelWidth = 0.0
pixelHeight = 0.0


def raster2array(rasterfn):
    raster = gdal.Open(rasterfn)
    band = raster.GetRasterBand(1)
    array = band.ReadAsArray()
    return array

def get_raster_info(rasterfn):
    global originX
    global originY
    global pixelWidth
    global pixelHeight
    raster = gdal.Open(rasterfn)
    geotransform = raster.GetGeoTransform()
    originX = geotransform[0]
    originY = geotransform[3]
    pixelWidth = geotransform[1]
    pixelHeight = geotransform[5]


def coord2pixelOffset(x,y):
    xOffset = int((x - originX)/pixelWidth)
    yOffset = int((y - originY)/pixelHeight)
    return xOffset,yOffset

def normalize(inputArray):
    normalizedArray = inputArray- np.min(inputArray[~np.isnan(inputArray)])
    normalizedArrayR = normalizedArray/ np.max(normalizedArray[~np.isnan(normalizedArray)])
    return normalizedArrayR

def createPath(costSurfaceArray,startIndexX,startIndexY,stopIndexX,stopIndexY):
    indices, weight = route_through_array(costSurfaceArray, (startIndexY,startIndexX), (stopIndexY,stopIndexX),geometric=True,fully_connected=True)
    indices = np.array(indices).T
    return indices

def getFeatures(gdf):
    # Function to parse features from GeoDataFrame in such a manner that rasterio wants them
    import json
    return [json.loads(gdf.to_json())['features'][0]['geometry']]

def route_path(costSurfaceArray, df_flowline, pathArray, streamcell_csv, flowlinefn, facfn,curvaturefn):
    i = 0
    geodesicPathsCellDic = {}
    for index, row in df_flowline.iterrows():
    	startXCoord = float(row['START_X'])
    	startYCoord = float(row['START_Y'])
    	endXCoord = float(row['END_X'])
    	endYCoord = float(row['END_Y'])
    	startIndexX, startIndexY = coord2pixelOffset(startXCoord,startYCoord)
    	stopIndexX, stopIndexY = coord2pixelOffset(endXCoord,endYCoord)
    	print(f'RAM usage before create path {i}: {psutil.virtual_memory()}')
    	print(' ')
    	indices = createPath(costSurfaceArray,startIndexX,startIndexY,stopIndexX,stopIndexY)
    	geodesicPathsCellDic[str(i)] = indices
    	i += 1
    	pathArray[indices[0],indices[1]] = 1
    	del indices
    
    NewgeodesicPathsCellDic, numberOfEndPoints, geodesicPathsCellList, keyList, \
                             jx, jy = Channel_Reconstruct(geodesicPathsCellDic, i)
    write_drainage_paths(geodesicPathsCellList, keyList, flowlinefn, curvaturefn)
    df_channel = pd.DataFrame(list(NewgeodesicPathsCellDic.items()),columns=['ID', 'PathCellList'])
    df_channel.to_csv(streamcell_csv, index=False)

def Channel_Reconstruct(geodesicPathsCellDic, numberOfEndPoints):
    df_channel = pd.DataFrame({'Y':[],'X':[]})
    for i in range(0,numberOfEndPoints):
        streamPathPixelList = geodesicPathsCellDic[str(i)]
        df_tempory = pd.DataFrame(streamPathPixelList.T, columns=['Y','X'])
        df_channel = pd.concat([df_channel,df_tempory])
    size_sr = df_channel.groupby(['Y','X']).size().to_dict()
    
    NewgeodesicPathsCellDic = {}
    StartpointList = []
    StartpointList2 = []
    jx = []
    jy = []
    k = 0
    #print(f'Entries in Original Dictionary: {len(geodesicPathsCellDic)}')
    for i in range(0,numberOfEndPoints):
        for j in range(0,geodesicPathsCellDic[str(i)][0].size):
            # If Statement: Checking if the cell being looped through has an index of zero.
            #               If yes, append it to the starting point list.

            if j==0:
                if i!= 0:
                    k += 1
                StartpointList.append([geodesicPathsCellDic[str(i)][0,j],geodesicPathsCellDic[str(i)][1,j]])
                NewgeodesicPathsCellDic[str(k)] = [[geodesicPathsCellDic[str(i)][0,j]],[geodesicPathsCellDic[str(i)][1,j]]]            
                StartpointList2.append([geodesicPathsCellDic[str(i)][0,j],geodesicPathsCellDic[str(i)][1,j]])  
           # Checking if the path cell at the current iteration is the same as the
           # previous iteration. If it is, append to the 'NewgeodesicPathsCellDic'.
            else:
                if size_sr[geodesicPathsCellDic[str(i)][0,j],geodesicPathsCellDic[str(i)][1,j]] == size_sr[geodesicPathsCellDic[str(i)][0,j-1],geodesicPathsCellDic[str(i)][1,j-1]]:
                    NewgeodesicPathsCellDic[str(k)][0].append(geodesicPathsCellDic[str(i)][0,j])
                    NewgeodesicPathsCellDic[str(k)][1].append(geodesicPathsCellDic[str(i)][1,j])
                    
                #elif size_sr[geodesicPathsCellDic[str(i)][0,j],geodesicPathsCellDic[str(i)][1,j]] != size_sr[geodesicPathsCellDic[str(i)][0,j-1],geodesicPathsCellDic[str(i)][1,j-1]]:
                #    NewgeodesicPathsCellDic[str(k)][0].append(geodesicPathsCellDic[str(i)][0,j])
                #    NewgeodesicPathsCellDic[str(k)][1].append(geodesicPathsCellDic[str(i)][1,j])
                
                # When this condition is satisfied, additional start points are added to the 
                # 'StartpointList' variable. This leads to unwanted segmentation of the
                # extracted channel network.
                else:
                    if [geodesicPathsCellDic[str(i)][0,j],geodesicPathsCellDic[str(i)][1,j]] not in StartpointList:
                        continue
                    else:
                        NewgeodesicPathsCellDic[str(k)][0].append(geodesicPathsCellDic[str(i)][0,j])
                        NewgeodesicPathsCellDic[str(k)][1].append(geodesicPathsCellDic[str(i)][1,j])
                        k += 1
                        break
    NewgeodesicPathsCellList = []
    keyList = []
    print(StartpointList)
    for key in list(NewgeodesicPathsCellDic.keys()):
        NewgeodesicPathsCellList.append(np.asarray(NewgeodesicPathsCellDic[key]))
        keyList.append(key)
    numberOfEndPoints = len(StartpointList2)
    print(f'Number of endpoints: {numberOfEndPoints}')
    
    return NewgeodesicPathsCellDic, numberOfEndPoints, NewgeodesicPathsCellList,keyList, jx, jy


def write_drainage_paths(geodesicPathsCellList, keyList, flowlinefn, curvaturefn):
    driver = ogr.GetDriverByName("ESRI Shapefile")
    data_source = driver.CreateDataSource(flowlinefn)
    ds = gdal.Open(curvaturefn, gdal.GA_ReadOnly)
    geotransform = ds.GetGeoTransform()
    inputwktInfo = ds.GetProjection()
    srs = osr.SpatialReference()
    gtf = geotransform
    georef = inputwktInfo
    srs.ImportFromWkt(georef)
    layer = data_source.CreateLayer(flowlinefn,\
                                    srs, ogr.wkbLineString)
    field_name = ogr.FieldDefn("Type", ogr.OFTString)
    field_name.SetWidth(24)
    layer.CreateField(field_name)
    layer.CreateField(ogr.FieldDefn("HYDROID", ogr.OFTInteger))
    for i in range(0,len(geodesicPathsCellList)):
        # Project the linepoints to appropriate projection
        xx = geodesicPathsCellList[i][1]
        yy = geodesicPathsCellList[i][0]
        # Project the xx, and yy points
        xxProj = float(gtf[0])+ \
                    float(gtf[1]) * np.array(xx) + 0.5 * pixelWidth
        yyProj = float(gtf[3])+ \
                    float(gtf[5])*np.array(yy) + 0.5 * pixelHeight
        # create the feature
        feature = ogr.Feature(layer.GetLayerDefn())
        # Set the attributes using the values
        feature.SetField("Type", 'ChannelNetwork')
        feature.SetField("HYDROID", keyList[i])
        # create the WKT for the feature using Python string formatting
        line = ogr.Geometry(ogr.wkbLineString)            
        for j in range(0,len(xxProj)):
            line.AddPoint(xxProj[j],yyProj[j])
        #print(f'xxProj: {len(xxProj)}')
        # Create the point from the Well Known Txt
        #lineobject = line.ExportToWkt()
        # Set the feature geometry using the point
        feature.SetGeometryDirectly(line)
        # Create the feature in the layer (shapefile)
        layer.CreateFeature(feature)
        # Destroy the feature to free resources
        feature.Destroy()
    # Destroy the data source to free resources
    data_source.Destroy()

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
    del outband
    
    
def main():
    geofloodHomeDir,projectName,DEM_name,chunk_status,input_fn,output_fn,hr_status = cfg_finder()
    geofloodResultsDir = os.path.join(geofloodHomeDir, output_fn,
                                     "GIS", projectName)
    # Read in parameters that could potentially be used in cost function.
    Name_path = os.path.join(geofloodResultsDir, DEM_name)    	
    flowline_csv = Name_path + '_endPoints.csv'
    curvaturefn = Name_path + '_curvature.tif'
    facfn = Name_path + '_fac.tif'
    hr_fn = Name_path + '_NHD_HR.tif'
    handfn = Name_path + '_NegaHand.tif'
    flowlinefn = Name_path + '_channelNetwork.shp'
    costsurfacefn = Name_path + '_cost.tif'
    pathfn = Name_path + '_path.tif'
    streamcell_csv = Name_path + '_streamcell.csv'
    src_fac = rasterio.open(facfn)
    src_curv = rasterio.open(curvaturefn)
    src_neghand = rasterio.open(handfn)
    if (os.path.exists(hr_fn)) and (hr_status==1): # HR raster from hr_raster.py script
    	src_hr = rasterio.open(hr_fn)

    dem_shape = src_curv.shape
    print(f'Chunk status: {chunk_status}')
    dem_bytes = src_curv.read(1).nbytes
    dem_limit = 1_500_000_000
    print(f'DEM Size: {round(np.float(dem_bytes)/10**9,3)} GB')
    if (dem_bytes>=dem_limit) and (chunk_status==1): # Default setting
    	print("Chunking DEM")
    	tot_chunks = math.ceil(np.float(dem_bytes)/(10**9))
    	print(f'Number of Chunks: {tot_chunks}')
    elif (dem_bytes<dem_limit) and (chunk_status==1):
    	print("DEM not big enough to chunk")
    	tot_chunks = 1
    else:
    	print("Not attempting to chunk DEM")
    	tot_chunks = 1
    row_iter = 1
    sample_rows = math.ceil(src_fac.shape[0]/tot_chunks) # Chunk by the row
    sample_cols = src_fac.shape[1]            
    costsurfaceArray = np.zeros(shape=src_fac.shape)
    cost_list = []
    # Chunking of rasters. If tot_chunks = 1, the entire raster will be processed at one time.
    for row_iter in range (1,tot_chunks+1):
    	facArray = src_fac.read(1,window=Window(0,(sample_rows*row_iter-sample_rows),sample_cols,sample_rows))
    	curvatureArray = src_curv.read(1,window=Window(0,(sample_rows*row_iter-sample_rows),sample_cols,sample_rows))
    	if (os.path.exists(hr_fn) and hr_status==1):
    		hr_Array = src_hr.read(1,window=Window(0,(sample_rows*row_iter-sample_rows),sample_cols,sample_rows))
    		hr_Array = hr_Array.astype(np.uint8)
    		if (row_iter==1):
    			print('Found HR_Flowline Raster')
    	handArray = src_neghand.read(1,window=Window(0,(sample_rows*row_iter-sample_rows),sample_cols,sample_rows))
    	
    	# FAC Calculations
    	facArray = np.log(facArray)
    	facArray = normalize(facArray)
    	facArray = facArray.astype(np.float32)
    	flowMean = np.mean(facArray[~np.isnan(facArray[:])])

    	# Curvature
    	curvatureArray = np.where((curvatureArray<-10) | (curvatureArray>10),np.nan,curvatureArray) 
    	curvatureArray = normalize(curvatureArray)
    	# The np where operation above is one last check/method to remove likely nan pixels
     	# that have not been flagged as nan. Typical curvature values are between -2 to 2 (Geometric) or -5 to 5 (laplacian)    	
    	
	# If the hr_extraction is found in the outputs folder, include in the cost function.
    	if (os.path.exists(hr_fn)) and (hr_status==1):
    		if (row_iter==1):
    			print('Calculating cost with NHD HR raster as a parameter.')
    		cost = 1/(curvatureArray*flowMean+facArray+0.75*handArray+hr_Array)
    	elif (not os.path.exists(hr_fn)) and (hr_status==1):
    		if (row_iter==1):
    			print('Could not find NHD HR raster. Calculating cost with out it.')
    		cost = 1/(curvatureArray*flowMean+facArray+0.75*handArray)
    	elif (os.path.exists(hr_fn)) and (hr_status==0):
    		if (row_iter==1):
    			print("Found HR raster, but 'hr_flowline' variable in project cfg is set to 0. \
Calculate cost without HR.")
    		cost = 1/(curvatureArray*flowMean+facArray+0.75*handArray)
    	else:
    		if (row_iter==1):
    			print('Not using NHD HR Raster in cost function')
    		cost = 1/(curvatureArray*flowMean+facArray+0.75*handArray)

    	cost_list.append(cost)
    	row_iter += 1
    	del facArray, curvatureArray, cost, handArray
    	if (os.path.exists(hr_fn)) and (hr_status==1):
    		del hr_Array
    	
    costsurfaceArray = cost_list
    del cost_list
    gc.collect()
    costsurfaceArray = np.concatenate(costsurfaceArray,axis=0).astype(np.float32)
    print(f'Cost shape: {costsurfaceArray.shape}')
    assert costsurfaceArray.shape[0] == dem_shape[0]
    assert costsurfaceArray.shape[1] == dem_shape[1]
    costQuantile = np.quantile(costsurfaceArray[~np.isnan(costsurfaceArray[:])],.025)
    
    array2raster(costsurfacefn,facfn,costsurfaceArray,gdal.GDT_Float32)
    
    costsurfaceArray[np.isnan(costsurfaceArray)] = 100000
    # Threshold cost	
    costsurfaceArray = np.where(costsurfaceArray<costQuantile,costsurfaceArray,100000)
    # Check memory usage
    get_raster_info(costsurfacefn)
    df_flowline = pd.read_csv(flowline_csv)    	
    pathArray = np.zeros_like(costsurfaceArray,dtype=np.uint8)
    costsurfaceArray = costsurfaceArray.astype(np.float32)
    route_path(costsurfaceArray, df_flowline, pathArray, streamcell_csv, flowlinefn, facfn,curvaturefn)

    array2raster(pathfn,costsurfacefn,pathArray,gdal.GDT_Byte)
    
if __name__ == '__main__':
    t0 = perf_counter()
    main()
    t1 = perf_counter()
    print(("time taken to retrace flowlines:", t1-t0, " seconds"))