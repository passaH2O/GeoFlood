import gdal, osr
from osgeo import ogr
from skimage.graph import route_through_array
import numpy as np
import pandas as pd
from pygeonet_rasterio import *

originX = 0.0
originY = 0.0
pixelWidth = 0.0
pixelHeight = 0.0


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
    NewgeodesicPathsCellDic, numberOfEndPoints, geodesicPathsCellList, jx, jy = Channel_Reconstruct(geodesicPathsCellDic,
                                                                                                    i)
    write_drainage_paths(geodesicPathsCellList, flowlinefn, skeletonfn)
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
    for key in NewgeodesicPathsCellDic.keys():
        NewgeodesicPathsCellList.append(np.asarray(NewgeodesicPathsCellDic[key]))
    numberOfEndPoints = len(StartpointList)
    return NewgeodesicPathsCellDic, numberOfEndPoints, NewgeodesicPathsCellList, jx, jy


def write_drainage_paths(geodesicPathsCellList, flowlinefn, skeletonfn):
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
    for i in xrange(0,len(geodesicPathsCellList)):
        # Project the linepoints to appropriate projection
        xx = geodesicPathsCellList[i][1]
        yy = geodesicPathsCellList[i][0]
        # Project the xx, and yy points
        xxProj = float(gtf[0])+ \
                    float(gtf[1]) * np.array(xx)
        yyProj = float(gtf[3])+ \
                    float(gtf[5])*np.array(yy)
        # create the feature
        feature = ogr.Feature(layer.GetLayerDefn())
        # Set the attributes using the values
        feature.SetField("Type", 'ChannelNetwork')
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
    outfilepath = Parameters.geonetResultsDir
    DEM_name = Parameters.demFileName.split('.')[0]
    curvaturefn = DEM_name + '_curvature.tif'
    facfn = DEM_name + '_fac.tif'
    handfn = DEM_name + '_hand.tif'
    skeletonfn = DEM_name + '_skeleton.tif'
    flowlinefn = DEM_name + '_channelNetwork.shp'
    costsurfacefn = DEM_name + '_cost.tif'
    pathfn = DEM_name + '_path.tif'
    flowlineendpoint_csv = DEM_name + '_endPoints.csv'
    streamcell_csv = DEM_name + '_streamcell.csv'
    facArray = read_geotif_generic(outfilepath, facfn)
    facArray = np.log10(facArray)
    facArray = normalize(facArray)
    flowMean = np.mean(facArray[~np.isnan(facArray[:])])
    curvatureArray = read_geotif_generic(outfilepath, curvaturefn)
    curvatureArray = normalize(curvatureArray)
    skeletonArray = read_geotif_generic(outfilepath, skeletonfn)
    costSurfaceArray = 1.0/(facArray+flowMean*curvatureArray+flowMean*skeletonArray)
    handfn = os.path.join(outfilepath, handfn)
    if os.path.exists(handfn):
        print True
        handArray = read_geotif_generic(outfilepath, handfn)
        costSurfaceArray = 1.0/(facArray+curvatureArray+skeletonArray+handArray)
    # write_geotif_generic(costSurfaceArray, outfilepath, costsurfacefn)
    costsurfacefn = os.path.join(outfilepath, costsurfacefn)
    facfn = os.path.join(outfilepath, facfn)
    array2raster(costsurfacefn,facfn,costSurfaceArray,gdal.GDT_Float32)
    costSurfaceArray[np.isnan(costSurfaceArray)] = 10000
    get_raster_info(costsurfacefn)
    flowlineendpoint_csv = os.path.join(outfilepath, flowlineendpoint_csv)
    df_flowline = pd.read_csv(flowlineendpoint_csv)
    pathArray = np.zeros_like(costSurfaceArray)
    streamcell_csv = os.path.join(outfilepath, streamcell_csv)
    flowlinefn = os.path.join(outfilepath, flowlinefn)
    skeletonfn = os.path.join(outfilepath, skeletonfn)
    route_path(costSurfaceArray, df_flowline, pathArray, streamcell_csv, flowlinefn, skeletonfn)
    # write_geotif_generic(pathArray, outfilepath, pathfn)
    pathfn = os.path.join(outfilepath, pathfn)
    array2raster(pathfn,costsurfacefn,pathArray,gdal.GDT_Byte)
    

if __name__ == "__main__":
    main()
