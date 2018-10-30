import numpy as np
import pandas as pd
import numpy.ma as npma
from time import clock
from pygeonet_plot import *
from pygeonet_rasterio import *
from pygeonet_vectorio import *

# Compute discrete geodesics
def compute_discrete_geodesic(geodesicDistanceArray,skeletonEndPoint,doTrueGradientDescent,num):
    #print 'computing discrete geodesics'
    # Extract a discrete geodesic path in 2D
    # D = geodesic distance matrix
    # x = channel head or start point
    # path = variable that stores the pixel values of the stream line.
    skeletonEndPoint = skeletonEndPoint[:]
    #print skeletonEndPoint[:]
    streamPathPixelList = skeletonEndPoint[:]
    #print 'skeletonEndPoint',skeletonEndPoint
    # Creating the 8 cell neighbor moves
    tempArrayDxMoves = [1, -1, 0, 0, 1, -1, 1, -1]
    tempArrayDyMoves = [0, 0, 1, -1, 1, -1, -1, 1]
    tempArray = [tempArrayDxMoves,tempArrayDyMoves]
    # Get the geodesic value for the channel head
    channelHeadGeodesicDistance = geodesicDistanceArray[skeletonEndPoint[0],skeletonEndPoint[1]]
    #print 'channelHeadGeodesicDistance',channelHeadGeodesicDistance
    # Get the size of the geodesic distance
    geodesicDistanceArraySize = geodesicDistanceArray.shape
    #print geodesicDistanceArraySize
    # While we find a geodesic distance less then previous value
    while True:
        cardinalDxMoves = [1, -1, 0, 0]
        cardinalDyMoves = [0, 0, 1, -1]
        diagonalDxMoves = [1, -1, 1, -1]
        diagonalDyMoves = [1, -1, -1, 1]
        cardinalAllPossibleMoves = [cardinalDxMoves,cardinalDyMoves]
        diagonalAllPossibleMoves = [diagonalDxMoves,diagonalDyMoves]
        tempStreamPathPixelList = streamPathPixelList[:,-1]
        #print tempStreamPathPixelList
        tempStreamPathPixelListA = np.array([[tempStreamPathPixelList[0]],\
                                             [tempStreamPathPixelList[1]]])
        cardinalSkeletonEndPoint = np.repeat(tempStreamPathPixelListA,4,axis=1)+\
                                      cardinalAllPossibleMoves
        diagonalSkeletonEndPoint = np.repeat(tempStreamPathPixelListA,4,axis=1)+\
                                   diagonalAllPossibleMoves
        r1 = cardinalSkeletonEndPoint.tolist()[0]
        r2 = cardinalSkeletonEndPoint.tolist()[1]
        r3 = diagonalSkeletonEndPoint.tolist()[0]
        r4 = diagonalSkeletonEndPoint.tolist()[1]

        neighborPixelSkeletonEndPointList = np.array([r1 + r3,r2 + r4])

        r5 = neighborPixelSkeletonEndPointList.tolist()[0]
        r6 = neighborPixelSkeletonEndPointList.tolist()[1]

        # Get the indices which are not on boundary
        cardinalAllowedIndex0 = np.array([cardinalSkeletonEndPoint[0,:] > 0] and\
                               [cardinalSkeletonEndPoint[0,:] < geodesicDistanceArraySize[0]])
        cardinalAllowedIndex1 = np.array([cardinalSkeletonEndPoint[1,:] > 0] and\
                               [cardinalSkeletonEndPoint[1,:] < geodesicDistanceArraySize[1]])        
        cardinalAllowedIndex = cardinalAllowedIndex0 * cardinalAllowedIndex1
        
        diagonalAllowedIndex0 = np.array([diagonalSkeletonEndPoint[0,:] > 0] and \
                               [diagonalSkeletonEndPoint[0,:] < geodesicDistanceArraySize[0]])
        diagonalAllowedIndex1 = np.array([diagonalSkeletonEndPoint[1,:] > 0] and\
                               [diagonalSkeletonEndPoint[1,:] < geodesicDistanceArraySize[1]])
        diagonalAllowedIndex = diagonalAllowedIndex0 * diagonalAllowedIndex1
        
        allAllowedIndex0 = np.array([neighborPixelSkeletonEndPointList[0,:] > 0] and\
                    [neighborPixelSkeletonEndPointList[0,:] < geodesicDistanceArraySize[0]])        
        allAllowedIndex1= np.array([neighborPixelSkeletonEndPointList[1,:] > 0] and\
                    [neighborPixelSkeletonEndPointList[1,:] < geodesicDistanceArraySize[1]])
        allAllowedIndex = allAllowedIndex0 * allAllowedIndex1
        
        #print cardinalAllowedIndex[0]
        #print diagonalAllowedIndex[0]
        #print allAllowedIndex[0]

        # Now remove neighbors that are no boundary
        # build the true false array
        tfCarray = np.array([cardinalAllowedIndex[0],cardinalAllowedIndex[0]])
        tfCarrayMask = np.zeros((tfCarray.shape))
        tfCarrayMask[tfCarray==False]=1
        popinfC = np.where(tfCarray[0,:]==False)
        #print popinfC
        
        tfDarray = np.array([diagonalAllowedIndex[0],diagonalAllowedIndex[0]])
        tfDarrayMask = np.zeros((tfDarray.shape))
        tfDarrayMask[tfDarray==False]=1
        popinfD = np.where(tfDarray[0,:]==False)
        #print popinfD
        
        tfAarray = np.array([allAllowedIndex[0],allAllowedIndex[0]])
        tfAarrayMask = np.zeros((tfAarray.shape))
        tfAarrayMask[tfAarray==False]=1
        popinfA = np.where(tfAarray[0,:]==False)
        #print popinfA
        
        # Now remove the false indices from our neighborhood matrix
        # Now arrange the arrays above
        cardinalSkeletonEndPointAllowed = npma.masked_array(cardinalSkeletonEndPoint,\
                                                            mask=tfCarrayMask)
        diagonalSkeletonEndPointAllowed = npma.masked_array(diagonalSkeletonEndPoint,\
                                                            mask=tfDarrayMask)
        neighborPixelSkeletonEndPointListAllowed=npma.masked_array(neighborPixelSkeletonEndPointList,\
                                                            mask=tfAarrayMask)

        rw1 = neighborPixelSkeletonEndPointListAllowed[0,:]
        rw2 = neighborPixelSkeletonEndPointListAllowed[1,:]
        rw3 = cardinalSkeletonEndPointAllowed[0,:]
        rw4 = cardinalSkeletonEndPointAllowed[1,:]
        rw5 = diagonalSkeletonEndPointAllowed[0,:]
        rw6 = diagonalSkeletonEndPointAllowed[1,:]
        # Get the minimum value of geodesic distance in the 8 cell neighbor
        # Get the values of D(I) and adjust values for diagonal elements
        try:
            allGeodesicDistanceList = np.array(geodesicDistanceArray[rw1[~rw1.mask],\
                rw2[~rw2.mask]])
            # new line   
            cardinalPixelGeodesicDistanceList = np.array(geodesicDistanceArray[rw3[~rw3.mask],\
                rw4[~rw4.mask]])
            diagonalPixelGeodesicDistanceList= np.array(geodesicDistanceArray[rw5[~rw5.mask],\
                rw6[~rw6.mask]])
        except:
            print neighborPixelSkeletonEndPointList
            print allAllowedIndex
            print allGeodesicDistanceList
            print popinfC
            print popinfD
            print popinfA
            print rw1,rw2,rw3,rw4,rw5,rw6
            print rw1[~rw1.mask]
            print rw2[~rw2.mask]
        #print allGeodesicDistanceList
        #print cardinalPixelGeodesicDistanceList
        #print diagonalPixelGeodesicDistanceList
        # We have to insert np.nan values for masked values
        allFinal = np.zeros((1,8))
        #print popinfA
        allFinal[0,popinfA[0]]= np.nan
        aF = 0
        cardinalFinal = np.zeros((1,4))
        #print popinfC
        cardinalFinal[0,popinfC[0]]= np.nan
        cF = 0
        diagonalFinal = np.zeros((1,4))
        #print popinfD
        diagonalFinal[0,popinfD[0]] = np.nan
        dF = 0

        #print allFinal,cardinalFinal,diagonalFinal
        for aFi in xrange(0,8):
            if ~np.isnan(allFinal[0,aFi]):
                allFinal[0,aFi] = allGeodesicDistanceList[aF]
                aF = aF+1
        #--------
        for cFi in xrange(0,4):
            if ~np.isnan(cardinalFinal[0,cFi]):
                cardinalFinal[0,cFi] = cardinalPixelGeodesicDistanceList[cF]
                cF = cF+1
        #--------
        for dFi in xrange(0,4):
            if ~np.isnan(diagonalFinal[0,dFi]):
                diagonalFinal[0,dFi] = diagonalPixelGeodesicDistanceList[dF]
                dF = dF+1
        #--------
        del allGeodesicDistanceList,  cardinalPixelGeodesicDistanceList,\
            diagonalPixelGeodesicDistanceList

        allGeodesicDistanceList = allFinal
        cardinalPixelGeodesicDistanceList = cardinalFinal
        diagonalPixelGeodesicDistanceList = diagonalFinal
        #print allGeodesicDistanceList
        #print cardinalPixelGeodesicDistanceList
        #print diagonalPixelGeodesicDistanceList
        #stop
        # for cells in horizontal and vertical positions to the
        # current cell
        cardinalPixelGeodesicDistanceList = channelHeadGeodesicDistance - \
                                            cardinalPixelGeodesicDistanceList
        # for cells in the diagonal position to the current cell
        diagonalPixelGeodesicDistanceList = (channelHeadGeodesicDistance - \
                                            diagonalPixelGeodesicDistanceList)/np.sqrt(2)
        tcL = cardinalPixelGeodesicDistanceList.tolist()
        tdL = diagonalPixelGeodesicDistanceList.tolist()
        neighborPixelGeodesicDistanceList = np.array(tcL[0]+tdL[0])
        
        #print type(cardinalPixelGeodesicDistanceList)
        #print tcL[0] + tdL[0]
        #print diagonalPixelGeodesicDistanceList
        #print neighborPixelGeodesicDistanceList
        
        # get the index of the maximum geodesic array
        chosenGeodesicIndex = np.argmax(neighborPixelGeodesicDistanceList)
        #print 'chosenGeodesicIndex',chosenGeodesicIndex
        # This is required to break out of the while loop
        chosenGeodesicDistanceFromAll = np.amin(allGeodesicDistanceList)
        #print 'neighborPixelSkeletonEndPointList',neighborPixelSkeletonEndPointList
        neighborPixelSkeletonEndPointList = neighborPixelSkeletonEndPointList[:,chosenGeodesicIndex]
        #print neighborPixelSkeletonEndPointList
        #stop
        if chosenGeodesicDistanceFromAll > channelHeadGeodesicDistance:
            #print "greater geo distance"
            #print channelHeadGeodesicDistance
            break
        elif np.isnan(chosenGeodesicDistanceFromAll):
            print "equal NaN"
            break
        #print 'before assig:',channelHeadGeodesicDistance
        channelHeadGeodesicDistance = chosenGeodesicDistanceFromAll
        #print 'afetr assig:',channelHeadGeodesicDistance
        #print channelHeadGeodesicDistance
        # Finally add the value of neighborPixelSkeletonEndPointList
        # to path list
        b = np.array([[neighborPixelSkeletonEndPointList[0]],\
                      [neighborPixelSkeletonEndPointList[1]]])
        #print 'b',b
        streamPathPixelList = np.hstack((streamPathPixelList,b))
    #print 'streamPathPixelList',streamPathPixelList
    #stop
    #print streamPathPixelList, streamPathPixelList.shape
    return streamPathPixelList

def compute_discrete_geodesic_v1():
    # this a new version using r.drain to extract discrete goedesics
    gisbase = os.environ['GISBASE']
    gisdbdir = Parameters.gisdbdir
    locationGeonet = 'geonet'
    mapsetGeonet = 'geonetuser'
    print gsetup.init(gisbase, gisdbdir, locationGeonet, mapsetGeonet)
    # Read the filtered DEM
    print 'r.in.gdal'
    outfilepathgeodesic = Parameters.geonetResultsDir
    outfilenamegeodesic = Parameters.demFileName
    outfilenamegeodesic = outfilenamegeodesic.split('.')[0]+'_geodesicDistance.tif'
    inputgeodesictifile = outfilepathgeodesic +'\\'+outfilenamegeodesic
    print 'importing goedesic tif: ',inputgeodesictifile
    print g.run_command('r.in.gdal', input=inputgeodesictifile, \
                        output=outfilenamegeodesic,overwrite=True)
    
    # The maximum number of points is 1024
    # --- have to add a check---
    # -- seems to run for large point shapefiles without fail.
    
    print 'importing channel heads shape file'
    channeheadsshapefileName = Parameters.pointshapefileName
    inputshapefilepath = Parameters.pointFileName
    print g.run_command('v.in.ogr',input = inputshapefilepath,\
                        layer=channeheadsshapefileName,output=channeheadsshapefileName,\
                        geometry='Point')
    
    print 'executing r.drain'
    print g.run_command('r.drain',input=outfilenamegeodesic,\
                        output='discretegeodesicsras',\
                        start_points=channeheadsshapefileName)
    print 'thining the discrete geodesic raster'
    print g.run_command('r.thin',input='discretegeodesicsras',\
                        output='discretegeodesicsrasthin')
    
    print 'converting the raster geodesic to vector map'
    print g.run_command('r.to.vect',input = 'discretegeodesicsrasthin',\
                        output='discretegeovec', type='line')

##    g.run_command('v.net',input='discretegeovec',output='networknode',operation='nodes')
##    g.run_command('v.out.ogr', input= 'networknode',type='point',layer='2',\
##                  output=Parameters.geonetResultsDir+"Test.shp",\
##                  format='ESRI_Shapefile')
    
    print 'exporting the geodesics as shapefile'
    print g.run_command('v.out.ogr', input= 'discretegeovec',\
                        output=Parameters.drainagelineFileName,\
                        format='ESRI_Shapefile')
    print 'completed discrete geodesics'
    # ---draining algorithm finished


def Channel_Reconstruct(geodesicPathsCellDic, numberOfEndPoints):
    df_channel = pd.DataFrame({'Y':[],'X':[]})
    for i in range(0,numberOfEndPoints):
        streamPathPixelList = geodesicPathsCellDic[str(i)]
        df_tempory = pd.DataFrame(streamPathPixelList.T, columns=['Y','X'])
        df_channel = pd.concat([df_channel,df_tempory])
    size_sr = df_channel.groupby(['Y','X']).size()
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
    

def Channel_Definition(xx,yy,geodesicDistanceArray,basinIndexArray,flowDirectionsArray):
    # Do compute discrete geodesics
    ## compute_discrete_geodesic_v1()
    print 'Computing discrete geodesics'
    numberOfEndPoints = len(xx)
    geodesicPathsCellDic = {}
    reachCodeDirectory = np.zeros((2,numberOfEndPoints))
    outerbounds = geodesicDistanceArray.shape
    for i in range(0,numberOfEndPoints):
        print 'EndPoint# ',(i+1),'/',numberOfEndPoints
        xEndPoint = xx[i]
        yEndPoint = yy[i]
        skeletonEndPoint = np.array([[yEndPoint],[xEndPoint]]) 
        watershedLabel = basinIndexArray[yEndPoint,xEndPoint]
        print 'watershedLabel',watershedLabel
        watershedIndexList = basinIndexArray == watershedLabel
        geodesicDistanceArrayMask = np.zeros((geodesicDistanceArray.shape))
        geodesicDistanceArrayMask[watershedIndexList]= \
                            geodesicDistanceArray[watershedIndexList]
        geodesicDistanceArrayMask[geodesicDistanceArrayMask == 0]= np.Inf
        streamPathPixelList = compute_discrete_geodesic(geodesicDistanceArrayMask,
                                                        skeletonEndPoint,
                                                        defaults.doTrueGradientDescent,i)
        geodesicPathsCellDic[str(i)] = streamPathPixelList
    #print 'geodesicPathsCellList',geodesicPathsCellList
    NewgeodesicPathsCellDic, numberOfEndPoints, geodesicPathsCellList, jx, jy = Channel_Reconstruct(geodesicPathsCellDic,
                                                                                                    numberOfEndPoints)
    df_channel = pd.DataFrame(NewgeodesicPathsCellDic.items(),columns=['ID', 'PathCellList'])
    df_channel.to_csv(Parameters.streamcellFileName, index=False)
    if defaults.doPlot==1:
        channel_plot(flowDirectionsArray,
                     geodesicPathsCellList,
                     xx,yy,'flowDirectionsArray channel heads and streams')
    # Write stream network as shapefiles
    write_drainage_paths(geodesicPathsCellList)
    # Write stream junctions as shapefiles
    write_drainage_nodes(jx,jy,'Junction',Parameters.junctionFileName, Parameters.junctionshapefileName)
    return NewgeodesicPathsCellDic, numberOfEndPoints


def main():
    outfilepath = Parameters.geonetResultsDir
    demName = Parameters.demFileName.split('.')[0]
    basin_filename = demName+'_basins.tif'
    basinIndexArray = read_geotif_generic(outfilepath, basin_filename)
    fdr_filename = demName + '_fdr.tif'
    flowDirectionsArray = read_geotif_generic(outfilepath, fdr_filename)
    geodesic_filename = demName+'_geodesicDistance.tif'
    geodesicDistanceArray = read_geotif_generic(outfilepath, geodesic_filename)
    channelhead_filename = demName+'_channelHeads.tif'
    channelheadArray = read_geotif_generic(outfilepath, channelhead_filename)
    channelheadArray = np.where(channelheadArray==1)
    xx = channelheadArray[1]
    yy = channelheadArray[0]
    Channel_Definition(xx,yy, geodesicDistanceArray, basinIndexArray, flowDirectionsArray)
    
if __name__ == '__main__':
    t0 = clock()
    main()
    t1 = clock()
    print "time taken to complete channel definition is: ",t1-t0," seconds"
