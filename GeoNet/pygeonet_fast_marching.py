import numpy as np
from time import clock
import skfmm
from pygeonet_rasterio import *
from pygeonet_plot import *


def Fast_Marching_Start_Point_Identification(outlet_array, basinIndexArray):

    # Computing the percentage drainage areas
    print 'Computing percentage drainage area of each indexed basin'
    fastMarchingStartPointList = np.array(outlet_array)
    fastMarchingStartPointListFMMx = []
    fastMarchingStartPointListFMMy = []
    basinsUsedIndexList = np.zeros((len(fastMarchingStartPointList[0]),1))
    if not hasattr(Parameters, 'xDemSize'):
        Parameters.xDemSize = np.size(basinIndexArray,1)
    if not hasattr(Parameters, 'yDemSize'):
        Parameters.yDemSize = np.size(basinIndexArray,0)
    nx = Parameters.xDemSize
    ny = Parameters.yDemSize
    nDempixels = float(nx*ny)
    for label in range(0,len(fastMarchingStartPointList[0])):
        outletbasinIndex = basinIndexArray[fastMarchingStartPointList[0,label],
                                           fastMarchingStartPointList[1,label]]
        numelments = basinIndexArray[basinIndexArray==outletbasinIndex]
        percentBasinArea = float(len(numelments)) * 100/nDempixels
        print 'Basin: ',outletbasinIndex,\
              '@ : ',fastMarchingStartPointList[:,label],' #Elements ',len(numelments),\
              ' area ',percentBasinArea,' %'
        if percentBasinArea > defaults.thresholdPercentAreaForDelineation and\
           len(numelments) > Parameters.numBasinsElements:
            # Get the watersheds used
            basinsUsedIndexList[label]= label
            # Preparing the outlets used for fast marching in ROI
            fastMarchingStartPointListFMMx.append(fastMarchingStartPointList[1,label])
            fastMarchingStartPointListFMMy.append(fastMarchingStartPointList[0,label])
        # finishing Making outlets for FMM
    #Closing Basin area computation
    fastMarchingStartPointListFMM = np.array([fastMarchingStartPointListFMMy,\
                                                  fastMarchingStartPointListFMMx])
    return fastMarchingStartPointListFMM


# Normalize Input Array
def normalize(inputArray):
    normalizedArray = inputArray-np.min(inputArray[~np.isnan(inputArray)])
    normalizedArrayR = normalizedArray/np.max(normalizedArray[~np.isnan(normalizedArray)])
    return normalizedArrayR


def Curvature_Preparation(curvatureDemArray):
    # lets normalize the curvature first
    if defaults.doNormalizeCurvature ==1:
        print 'normalizing curvature'
        curvatureDemArray = normalize(curvatureDemArray)
        if defaults.doPlot == 1:
            raster_plot(curvatureDemArray, 'Curvature DEM')
        print 'Curvature min: ' ,str(np.min(curvatureDemArray[~np.isnan(curvatureDemArray)])), \
              ' exp(min): ',str(np.exp(3*np.min(curvatureDemArray[~np.isnan(curvatureDemArray)])))
        print 'Curvature max: ' ,str(np.max(curvatureDemArray[~np.isnan(curvatureDemArray)])),\
              ' exp(max): ',str(np.exp(3*np.max(curvatureDemArray[~np.isnan(curvatureDemArray)])))
    # set all the nan's to zeros before cost function is computed
    curvatureDemArray[np.isnan(curvatureDemArray)] = 0
    return curvatureDemArray


def Local_Cost_Computation(flowArray, flowMean,
                           skeletonFromFlowAndCurvatureArray,
                           curvatureDemArray):
    if hasattr(defaults, 'reciprocalLocalCostFn'):
        print 'Evaluating local cost func.'
        reciprocalLocalCostArray = eval(defaults.reciprocalLocalCostFn)
    else:
        print 'Evaluating local cost func. (default)'
        reciprocalLocalCostArray = flowArray + \
                                   (flowMean*skeletonFromFlowAndCurvatureArray)\
                                   + (flowMean*curvatureDemArray)
    if hasattr(defaults,'reciprocalLocalCostMinimum'):
        if defaults.reciprocalLocalCostMinimum != 'nan':
            reciprocalLocalCostArray[reciprocalLocalCostArray[:]\
                                 < defaults.reciprocalLocalCostMinimum]=1.0
    
    print '1/cost min: ', np.nanmin(reciprocalLocalCostArray[:]) 
    print '1/cost max: ', np.nanmax(reciprocalLocalCostArray[:])

    # Writing the reciprocal array
    outfilepath = Parameters.geonetResultsDir
    outfilename = Parameters.demFileName
    outfilename = outfilename.split('.')[0]+'_costfunction.tif'
    write_geotif_generic(reciprocalLocalCostArray,outfilepath,outfilename)
    return reciprocalLocalCostArray


def Fast_Marching(fastMarchingStartPointListFMM, basinIndexArray, flowArray, reciprocalLocalCostArray):
    # Fast marching
    print 'Performing fast marching'
    # Do fast marching for each sub basin
    geodesicDistanceArray = np.zeros((basinIndexArray.shape))
    geodesicDistanceArray[geodesicDistanceArray==0]=np.Inf
    for i in range(0,len(fastMarchingStartPointListFMM[0])):
        basinIndexList = basinIndexArray[fastMarchingStartPointListFMM[0,i],
                                         fastMarchingStartPointListFMM[1,i]]
        print 'basin Index:', basinIndexList
        print 'start point :', fastMarchingStartPointListFMM[:,i]
        maskedBasin = np.zeros((basinIndexArray.shape))
        maskedBasin[basinIndexArray==basinIndexList]=1
        maskedBasinFAC = np.zeros((basinIndexArray.shape))
        maskedBasinFAC[basinIndexArray==basinIndexList]=\
        flowArray[basinIndexArray==basinIndexList]
##        maskedBasinFAC[maskedBasinFAC==0]=np.nan
##        # Get the outlet of subbasin
##        maskedBasinFAC[np.isnan(maskedBasinFAC)]=0
        # outlets locations in projection of the input dataset
##        outletsxx = fastMarchingStartPointList[1,i]
##        outletsyy = fastMarchingStartPointList[0,i]
        # call the fast marching here
        phi = np.nan * np.ones((reciprocalLocalCostArray.shape))
        speed = np.ones((reciprocalLocalCostArray.shape))* np.nan
        phi[maskedBasinFAC!=0] = 1
        speed[maskedBasinFAC!=0] = reciprocalLocalCostArray[maskedBasinFAC!=0]
        phi[fastMarchingStartPointListFMM[0,i],
            fastMarchingStartPointListFMM[1,i]] =-1
        try:
            travelTimearray = skfmm.travel_time(phi, speed, dx=1)
        except IOError as e:            
            print 'Error in calculating skfmm travel time'
            print 'Error in catchment: ',basinIndexList
            print "I/O error({0}): {1}".format(e.errno, e.strerror)
            # setting travel time to empty array
            travelTimearray = np.nan * np.zeros((reciprocalLocalCostArray.shape))
            if defaults.doPlot == 1:
                raster_point_plot(speed, fastMarchingStartPointListFMM[:,i],
                                  'speed basin Index'+str(basinIndexList))
                #plt.contour(speed,cmap=cm.coolwarm)
                raster_point_plot(phi, fastMarchingStartPointListFMM[:,i],
                                  'phi basin Index'+str(basinIndexList))
        except ValueError:
            print 'Error in calculating skfmm travel time'
            print 'Error in catchment: ',basinIndexList
            print "Oops!  That was no valid number.  Try again..."
        geodesicDistanceArray[maskedBasin ==1]= travelTimearray[maskedBasin ==1]
    geodesicDistanceArray[geodesicDistanceArray==np.Inf]=np.nan
    # Plot the geodesic array
    if defaults.doPlot == 1:
        geodesic_contour_plot(geodesicDistanceArray,
                              'Geodesic distance array (travel time)')
    # Writing the geodesic distance array
    outfilepath = Parameters.geonetResultsDir
    demName = Parameters.demFileName.split('.')[0]
    outfilename = demName+'_geodesicDistance.tif'
    write_geotif_generic(geodesicDistanceArray, outfilepath, outfilename)
    return geodesicDistanceArray


def main():
    outfilepath = Parameters.geonetResultsDir
    demName = Parameters.demFileName.split('.')[0]
    outlet_filename = demName+'_outlets.tif'
    outlet_array = read_geotif_generic(outfilepath, outlet_filename)
    outlet_array = np.transpose(np.argwhere(~np.isnan(outlet_array)))
    basin_filename = demName+'_basins.tif'
    basinIndexArray = read_geotif_generic(outfilepath, basin_filename)
    curvature_filename = demName+'_curvature.tif'
    curvatureDemArray = read_geotif_generic(outfilepath, curvature_filename)
    fac_filename = demName + '_fac.tif'
    flowArray = read_geotif_generic(outfilepath, fac_filename)
    filteredDemArray = read_geotif_filteredDEM()
    flowArray[np.isnan(filteredDemArray)]=np.nan
    flowMean = np.mean(flowArray[~np.isnan(flowArray[:])])
    skeleton_filename = demName+'_skeleton.tif'
    skeletonFromFlowAndCurvatureArray = read_geotif_generic(outfilepath, skeleton_filename)
    # Making outlets for FMM
    fastMarchingStartPointListFMM = Fast_Marching_Start_Point_Identification(outlet_array, basinIndexArray)
    # Computing the local cost function
    print 'Preparing to calculate cost function'
    curvatureDemArray = Curvature_Preparation(curvatureDemArray)
    # Calculate the local reciprocal cost (weight, or propagation speed in the
    # eikonal equation sense).  If the cost function isn't defined, default to
    # old cost function.
    print 'Calculating local costs'
    reciprocalLocalCostArray = Local_Cost_Computation(flowArray, flowMean,
                                                      skeletonFromFlowAndCurvatureArray,
                                                      curvatureDemArray)
    # Compute the geodesic distance using Fast Marching Method
    geodesicDistanceArray = Fast_Marching(fastMarchingStartPointListFMM, basinIndexArray, flowArray, reciprocalLocalCostArray)
    
    


if __name__ == '__main__':
    t0 = clock()
    main()
    t1 = clock()
    print "time taken to complete cost computation and fast marching:",
    t1-t0, " seconds"



