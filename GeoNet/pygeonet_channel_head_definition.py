import numpy as np
from scipy import ndimage
from time import clock
from pygeonet_rasterio import *
from pygeonet_vectorio import *
from pygeonet_plot import *


def Channel_Head_Definition(skeletonFromFlowAndCurvatureArray, geodesicDistanceArray):
    # Locating end points
    print 'Locating skeleton end points'
    structure = np.ones((3, 3))
    skeletonLabeledArray, skeletonNumConnectedComponentsList =\
                          ndimage.label(skeletonFromFlowAndCurvatureArray,
                                        structure=structure)
    """
     Through the histogram of skeletonNumElementsSortedList
     (skeletonNumElementsList minus the maximum value which
      corresponds to the largest connected element of the skeleton) we get the
      size of the smallest elements of the skeleton, which will likely
      correspond to small isolated convergent areas. These elements will be
      excluded from the search of end points.
    """
    print 'Counting the number of elements of each connected component'
    lbls = np.arange(1, skeletonNumConnectedComponentsList+1)
    skeletonLabeledArrayNumtuple = ndimage.labeled_comprehension(skeletonFromFlowAndCurvatureArray,\
                                                                 skeletonLabeledArray,\
                                                                 lbls,np.count_nonzero,\
                                                                 int,0)
    skeletonNumElementsSortedList = np.sort(skeletonLabeledArrayNumtuple)
    histarray,skeletonNumElementsHistogramX=np.histogram(\
        skeletonNumElementsSortedList[0:len(skeletonNumElementsSortedList)-1],
        int(np.floor(np.sqrt(len(skeletonNumElementsSortedList)))))
    if defaults.doPlot == 1:
        raster_plot(skeletonLabeledArray, 'Skeleton Labeled Array elements Array')
    # Create skeleton gridded array
    skeleton_label_set, label_indices = np.unique(skeletonLabeledArray, return_inverse=True)
    skeletonNumElementsGriddedArray = np.array([skeletonLabeledArrayNumtuple[x-1] for x in skeleton_label_set])[label_indices].reshape(skeletonLabeledArray.shape)
    if defaults.doPlot == 1:
        raster_plot(skeletonNumElementsGriddedArray,
                    'Skeleton Num elements Array')
    # Elements smaller than skeletonNumElementsThreshold are not considered in the
    # skeletonEndPointsList detection
    skeletonNumElementsThreshold = skeletonNumElementsHistogramX[2]
    print 'skeletonNumElementsThreshold',str(skeletonNumElementsThreshold)
    # Scan the array for finding the channel heads
    print 'Continuing to locate skeleton endpoints'
    skeletonEndPointsList = []
    nrows = skeletonFromFlowAndCurvatureArray.shape[0]
    ncols = skeletonFromFlowAndCurvatureArray.shape[1]
    for i in range(nrows):
        for j in range(ncols):
            if skeletonLabeledArray[i,j]!=0 \
               and skeletonNumElementsGriddedArray[i,j]>=skeletonNumElementsThreshold:
                # Define search box and ensure it fits within the DTM bounds
                my = i-1
                py = nrows-i
                mx = j-1
                px = ncols-j
                xMinus = np.min([defaults.endPointSearchBoxSize, mx])
                xPlus  = np.min([defaults.endPointSearchBoxSize, px])
                yMinus = np.min([defaults.endPointSearchBoxSize, my])
                yPlus  = np.min([defaults.endPointSearchBoxSize, py])
                # Extract the geodesic distances geodesicDistanceArray for pixels within the search box
                searchGeodesicDistanceBox = geodesicDistanceArray[i-yMinus:i+yPlus, j-xMinus:j+xPlus]
                # Extract the skeleton labels for pixels within the search box
                searchLabeledSkeletonBox = skeletonLabeledArray[i-yMinus:i+yPlus, j-xMinus:j+xPlus]
                # Look in the search box for skeleton points with the same label
                # and greater geodesic distance than the current pixel at (i,j)
                # - if there are none, then add the current point as a channel head
                v = searchLabeledSkeletonBox==skeletonLabeledArray[i,j]
                v1 = v * searchGeodesicDistanceBox > geodesicDistanceArray[i,j]
                v3 = np.where(np.any(v1==True,axis=0))
                if len(v3[0])==0:
                    skeletonEndPointsList.append([i,j])
    # For loop ends here
    skeletonEndPointsListArray = np.transpose(skeletonEndPointsList)
    if defaults.doPlot == 1:
        raster_point_plot(skeletonFromFlowAndCurvatureArray, skeletonEndPointsListArray,
                          'Skeleton Num elements Array with channel heads', cm.binary, 'ro')
    if defaults.doPlot == 1:
        raster_point_plot(geodesicDistanceArray, skeletonEndPointsListArray,
                          'Geodesic distance Array with channel heads', cm.coolwarm, 'ro')
    xx = skeletonEndPointsListArray[1]
    yy = skeletonEndPointsListArray[0]
    # Write shapefiles of channel heads
    write_drainage_nodes(xx,yy,"ChannelHead",
                         Parameters.pointFileName,Parameters.pointshapefileName)
    # Write raster of channel heads
    channelheadArray = np.zeros((geodesicDistanceArray.shape))
    channelheadArray[skeletonEndPointsListArray[0],
                     skeletonEndPointsListArray[1]] = 1
    outfilepath = Parameters.geonetResultsDir
    demName = Parameters.demFileName
    outfilename = demName.split('.')[0]+'_channelHeads.tif'
    write_geotif_generic(channelheadArray,\
                         outfilepath,outfilename)
    return xx, yy

def main():
    outfilepath = Parameters.geonetResultsDir
    demName = Parameters.demFileName.split('.')[0]
    skeleton_filename = demName+'_skeleton.tif'
    skeletonFromFlowAndCurvatureArray = read_geotif_generic(outfilepath, skeleton_filename)
    geodesic_filename = demName+'_geodesicDistance.tif'
    geodesicDistanceArray = read_geotif_generic(outfilepath, geodesic_filename)
    Channel_Head_Definition(skeletonFromFlowAndCurvatureArray, geodesicDistanceArray)


if __name__ == '__main__':
    t0 = clock()
    main()
    t1 = clock()
    print "time taken to complete channel head definition:", t1-t0, " seconds"
