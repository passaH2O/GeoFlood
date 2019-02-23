import os
import gdal, osr
from osgeo import ogr
from skimage.graph import route_through_array
import numpy as np
import pandas as pd
import ConfigParser
import inspect


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

    # create path
    indices, weight = route_through_array(costSurfaceArray, (startIndexY,startIndexX), (stopIndexY,stopIndexX),geometric=False,fully_connected=True)
    indices = np.array(indices).T
    return indices


def route_path(costSurfaceArray, df_flowline, pathArray, streamcell_csv, flowlinefn, skeletonfn):
    i = 0
    geodesicPathsCellDic = {}
    for index, row in df_flowline.iterrows():
        startXCoord = row['START_X']
        startYCoord = row['START_Y']
        endXCoord = row['END_X']
        endYCoord = row['END_Y']
        startIndexX, startIndexY = coord2pixelOffset(startXCoord,startYCoord)
        stopIndexX, stopIndexY = coord2pixelOffset(endXCoord,endYCoord)
        indices = createPath(costSurfaceArray,startIndexX,startIndexY,stopIndexX,stopIndexY)
        geodesicPathsCellDic[str(i)] = indices
        i += 1
        pathArray[indices[0], indices[1]] = 1
    NewgeodesicPathsCellDic, numberOfEndPoints, geodesicPathsCellList, keyList, \
                             jx, jy = Channel_Reconstruct(geodesicPathsCellDic, i)
    write_drainage_paths(geodesicPathsCellList, keyList, flowlinefn, skeletonfn)
    df_channel = pd.DataFrame(NewgeodesicPathsCellDic.items(),columns=['ID', 'PathCellList'])
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
    jx = []
    jy = []
    k = 0
    for i in range(0,numberOfEndPoints):
        for j in range(0,geodesicPathsCellDic[str(i)][0].size):
            if j==0:
                if i!= 0:
                    k += 1
                StartpointList.append([geodesicPathsCellDic[str(i)][0,j],geodesicPathsCellDic[str(i)][1,j]])
                NewgeodesicPathsCellDic[str(k)] = [[geodesicPathsCellDic[str(i)][0,j]],[geodesicPathsCellDic[str(i)][1,j]]]
            else:
                if size_sr[geodesicPathsCellDic[str(i)][0,j],geodesicPathsCellDic[str(i)][1,j]] == size_sr[geodesicPathsCellDic[str(i)][0,j-1],geodesicPathsCellDic[str(i)][1,j-1]]:
                    NewgeodesicPathsCellDic[str(k)][0].append(geodesicPathsCellDic[str(i)][0,j])
                    NewgeodesicPathsCellDic[str(k)][1].append(geodesicPathsCellDic[str(i)][1,j])
                else:
                    if [geodesicPathsCellDic[str(i)][0,j],geodesicPathsCellDic[str(i)][1,j]] not in StartpointList:
                        k += 1
                        jx.append(geodesicPathsCellDic[str(i)][1,j])
                        jy.append(geodesicPathsCellDic[str(i)][0,j])
                        NewgeodesicPathsCellDic[str(k-1)][0].append(geodesicPathsCellDic[str(i)][0,j])
                        NewgeodesicPathsCellDic[str(k-1)][1].append(geodesicPathsCellDic[str(i)][1,j])
                        NewgeodesicPathsCellDic[str(k)] = [[geodesicPathsCellDic[str(i)][0,j]],[geodesicPathsCellDic[str(i)][1,j]]]
                        StartpointList.append([geodesicPathsCellDic[str(i)][0,j], geodesicPathsCellDic[str(i)][1,j]])
                    else:
                        NewgeodesicPathsCellDic[str(k)][0].append(geodesicPathsCellDic[str(i)][0,j])
                        NewgeodesicPathsCellDic[str(k)][1].append(geodesicPathsCellDic[str(i)][1,j])
                        break
    NewgeodesicPathsCellList = []
    keyList = []
    for key in NewgeodesicPathsCellDic.keys():
        NewgeodesicPathsCellList.append(np.asarray(NewgeodesicPathsCellDic[key]))
        keyList.append(key)
    numberOfEndPoints = len(StartpointList)
    return NewgeodesicPathsCellDic, numberOfEndPoints, NewgeodesicPathsCellList,keyList, jx, jy


def write_drainage_paths(geodesicPathsCellList, keyList, flowlinefn, skeletonfn):
    driver = ogr.GetDriverByName("ESRI Shapefile")
    data_source = driver.CreateDataSource(flowlinefn)
    ds = gdal.Open(skeletonfn, gdal.GA_ReadOnly)
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
    for i in xrange(0,len(geodesicPathsCellList)):
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
        for j in xrange(0,len(xxProj)):
            line.AddPoint(xxProj[j],yyProj[j])
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


def main():
    config = ConfigParser.RawConfigParser()
    config.read(os.path.join(os.path.dirname(
        os.path.dirname(
            inspect.stack()[0][1])),
                             'GeoFlood.cfg'))
    geofloodHomeDir = config.get('Section', 'geofloodhomedir')
    projectName = config.get('Section', 'projectname')
    #geofloodHomeDir = "H:\GeoFlood"
    #projectName = "Test_Stream"
    geofloodResultsDir = os.path.join(geofloodHomeDir, "Outputs",
                                      "GIS", projectName)
    DEM_name = config.get('Section', 'dem_name')
    #DEM_name = "DEM"
    Name_path = os.path.join(geofloodResultsDir, DEM_name)
    flowline_csv = Name_path + '_endPoints.csv'
    curvaturefn = Name_path + '_curvature.tif'
    facfn = Name_path + '_fac.tif'
    skeletonfn = Name_path + '_skeleton.tif'
    handfn = Name_path + '_NegaHand.tif'
    flowlinefn = Name_path + '_channelNetwork.shp'
    costsurfacefn = Name_path + '_cost.tif'
    pathfn = Name_path + '_path.tif'
    streamcell_csv = Name_path + '_streamcell.csv'
    facArray = raster2array(facfn)
    facArray = np.log10(facArray)
    facArray = normalize(facArray)
    flowMean = np.mean(facArray[~np.isnan(facArray[:])])
    curvatureArray = raster2array(curvaturefn)
    curvatureArray = normalize(curvatureArray)
    skeletonArray = raster2array(skeletonfn)
    #costsurfaceArray = 1.0/(facArray+flowMean*curvatureArray+flowMean*skeletonArray)
    costsurfaceArray = 1.0/(facArray+curvatureArray+10*skeletonArray)
    if os.path.exists(handfn):
        handArray = raster2array(handfn)
        costsurfaceArray = 1.0/(facArray+curvatureArray+skeletonArray*10+handArray)
    array2raster(costsurfacefn,facfn,costsurfaceArray,gdal.GDT_Float32)
    costsurfaceArray[np.isnan(costsurfaceArray)] = 10000
    get_raster_info(costsurfacefn)
    df_flowline = pd.read_csv(flowline_csv)
    pathArray = np.zeros_like(costsurfaceArray)
    route_path(costsurfaceArray, df_flowline, pathArray, streamcell_csv, flowlinefn, skeletonfn)
    array2raster(pathfn,costsurfacefn,pathArray,gdal.GDT_Byte)
    

if __name__ == "__main__":
    main()
