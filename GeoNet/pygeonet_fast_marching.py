import numpy as np
import skfmm
from time import perf_counter
from pygeonet_rasterio import *
from pygeonet_plot import *
import time
from numba import njit
from numba import prange
import psutil
import dask
from dask.distributed import Client

def Fast_March_Setup(outlet_array, basinIndexArray):

    # Computing the percentage drainage areas
    print("Computing percentage drainage area of each indexed basin")
    fastMarchingStartPointList = np.array(outlet_array)
    fmmX = []
    fmmY = []
    basinsUsedIndexList = np.zeros((len(fastMarchingStartPointList[0]),1))
    if not hasattr(Parameters, 'xDemSize'):
        Parameters.xDemSize = np.size(basinIndexArray,1)
    if not hasattr(Parameters, 'yDemSize'):
        Parameters.yDemSize = np.size(basinIndexArray,0)
    nx = Parameters.xDemSize
    ny = Parameters.yDemSize
    nDempixels = float(nx*ny)
    basin_elements=Parameters.numBasinsElements
    threshold=defaults.thresholdPercentAreaForDelineation
    #n_test=basinIndexArray[fastMarchingStartPointList[0,:],
    #				fastMarchingStartPointList[1,:]]
    iter_total = np.arange(0,len(fastMarchingStartPointList[0])).size
    print(iter_total)
    return fastMarchingStartPointList, nDempixels,basin_elements, threshold, iter_total

def for_loop(iter_total):
    for i in range(iter_total):
        print(i)


@njit(parallel=True)
def Fast_Marching_Start_Point_Identification(outlet_array, basinIndexArray,fastMarchingStartPointList, nDempixels,basin_elements, threshold, iter_total):
    fmmX = []
    fmmY = []
    for label in prange(iter_total):
        #print(np.sum(basinIndexArray.ravel()==(label+1)))
        numelments = np.sum(basinIndexArray.ravel()==(label+1))
        
        percentBasinArea = numelments * 100.00001/nDempixels
        if (percentBasinArea > threshold) and (numelments > basin_elements):            
            fmmX.append(fastMarchingStartPointList[1,label])
            fmmY.append(fastMarchingStartPointList[0,label])
        
    return fmmX, fmmY

def fmm_list_creation(fmmY,fmmX):
    fastMarchingStartPointListFMM = np.array([fmmY,fmmX])
    del fmmY, fmmX
    return fastMarchingStartPointListFMM


# Normalize Input Array
def normalize(inputArray):
    normalizedArray = inputArray-np.min(inputArray[~np.isnan(inputArray)])
    normalizedArrayR = normalizedArray/np.max(normalizedArray[~np.isnan(normalizedArray)])
    return normalizedArrayR


def Curvature_Preparation(curvatureDemArray):
    # Normalize the curvature first
    if defaults.doNormalizeCurvature ==1:
        print('normalizing curvature')
        curvatureDemArray = normalize(curvatureDemArray)
        #if defaults.doPlot == 1:
        #    raster_plot(curvatureDemArray, 'Curvature DEM')
        print('Curvature min: ' ,str(np.min(curvatureDemArray[~np.isnan(curvatureDemArray)])), \
              ' exp(min): ',str(np.exp(3*np.min(curvatureDemArray[~np.isnan(curvatureDemArray)]))))
        print('Curvature max: ' ,str(np.max(curvatureDemArray[~np.isnan(curvatureDemArray)])),\
              ' exp(max): ',str(np.exp(3*np.max(curvatureDemArray[~np.isnan(curvatureDemArray)]))))
    # set all the nan's to zeros before cost function is computed
    curvatureDemArray[np.isnan(curvatureDemArray)] = 0 #################################
    return curvatureDemArray


def Local_Cost_Computation(flowArray, flowMean,
                           skeletonFromFlowAndCurvatureArray,
                           curvatureDemArray):
    if hasattr(defaults, 'reciprocalLocalCostFn'):
        print('Evaluating local cost func.')
        reciprocalLocalCostArray = eval(defaults.reciprocalLocalCostFn)
    else:
        print('Evaluating local cost func. (default)')
        reciprocalLocalCostArray = flowArray + \
                                   (flowMean*skeletonFromFlowAndCurvatureArray)\
                                   + (flowMean*curvatureDemArray)
    if hasattr(defaults,'reciprocalLocalCostMinimum'):
        if defaults.reciprocalLocalCostMinimum != 'nan':
            reciprocalLocalCostArray[reciprocalLocalCostArray[:]\
                                 < defaults.reciprocalLocalCostMinimum]=1.0
    
    print('1/cost min: ', np.nanmin(reciprocalLocalCostArray[:]))
    print('1/cost max: ', np.nanmax(reciprocalLocalCostArray[:]))

    # Writing the reciprocal array
    outfilepath = Parameters.geonetResultsDir
    outfilename = Parameters.demFileName
    outfilename = outfilename.split('.')[0]+'_costfunction.tif'
    write_geotif_generic(reciprocalLocalCostArray,outfilepath,outfilename)
    return reciprocalLocalCostArray

def Fast_Marching(fastMarchingStartPointListFMM, basinIndexArray, flowArray, reciprocalLocalCostArray):
    # Fast marching
    print('Performing fast marching')
    # Do fast marching for each sub basin
    geodesicDistanceArray = np.zeros((basinIndexArray.shape))
    geodesicDistanceArray[geodesicDistanceArray==0]=np.Inf
    for i in range(0,len(fastMarchingStartPointListFMM[0])):
        basinIndexList = basinIndexArray[fastMarchingStartPointListFMM[0,i],
                                         fastMarchingStartPointListFMM[1,i]]
        print('start point :', fastMarchingStartPointListFMM[:,i])
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
        #phi = np.nan * np.ones((reciprocalLocalCostArray.shape)) # old
        phi = np.zeros(reciprocalLocalCostArray.shape)
        #speed = np.ones((reciprocalLocalCostArray.shape))* np.nan # old
        speed = np.zeros(reciprocalLocalCostArray.shape)
        phi[maskedBasinFAC!=0] = 1
        speed[maskedBasinFAC!=0] = reciprocalLocalCostArray[maskedBasinFAC!=0]    
        phi[fastMarchingStartPointListFMM[0,i],
            fastMarchingStartPointListFMM[1,i]] = -1
        del maskedBasinFAC
        print(f'RAM usage before FMM {i}: {psutil.virtual_memory()}')
        try:
            travelTimearray = skfmm.travel_time(phi, speed, dx=.01)
        except IOError as e:            
            print('Error in calculating skfmm travel time')
            print('Error in catchment: ',basinIndexList)
            print("I/O error({0}): {1}".format(e.errno, e.strerror))
            # setting travel time to empty array
            travelTimearray = np.nan * np.zeros((reciprocalLocalCostArray.shape))
            #if defaults.doPlot == 1:
            #    raster_point_plot(speed, fastMarchingStartPointListFMM[:,i],
            #                      'speed basin Index'+str(basinIndexList))
                #plt.contour(speed,cmap=cm.coolwarm)
            #    raster_point_plot(phi, fastMarchingStartPointListFMM[:,i],
            #                      'phi basin Index'+str(basinIndexList))
        except ValueError:
            print('Error in calculating skfmm travel time')
            print('Error in catchment: ',basinIndexList)
            print("Oops!  That was no valid number.  Try again...")
        geodesicDistanceArray[maskedBasin ==1]= travelTimearray[maskedBasin ==1]
    geodesicDistanceArray[maskedBasin ==1]= travelTimearray[maskedBasin ==1]
    geodesicDistanceArray[geodesicDistanceArray==np.Inf]=np.nan
    # Plot the geodesic array
    #if defaults.doPlot == 1:
    #    geodesic_contour_plot(geodesicDistanceArray,
    #                          'Geodesic distance array (travel time)')
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
    outlet_array = read_geotif_generic(outfilepath, outlet_filename)[0]
    outlet_array = np.transpose(np.argwhere(~np.isnan(outlet_array)))
    basin_filename = demName+'_basins.tif'
    basinIndexArray = read_geotif_generic(outfilepath, basin_filename)[0]
    curvature_filename = demName+'_curvature.tif'
    curvatureDemArray = read_geotif_generic(outfilepath, curvature_filename)[0]
    fac_filename = demName + '_fac.tif'
    flowArray = read_geotif_generic(outfilepath, fac_filename)[0]
    filteredDemArray = read_geotif_filteredDEM()
    flowArray[np.isnan(filteredDemArray)]=np.nan
    flowMean = np.mean(flowArray[~np.isnan(flowArray[:])])
    skeleton_filename = demName+'_skeleton.tif'
    skeletonFromFlowAndCurvatureArray = read_geotif_generic(outfilepath, skeleton_filename)[0]

    # Initialize Parameters
    fastMarchingStartPointList,nDempixels,basin_elements, threshold, iter_total = Fast_March_Setup(outlet_array,basinIndexArray)

    # Making outlets for FMM
    t1 = time.perf_counter()
    fmmX,fmmY = Fast_Marching_Start_Point_Identification(outlet_array, basinIndexArray,fastMarchingStartPointList,nDempixels,basin_elements, threshold, iter_total)
    t2 = time.perf_counter()
    print(f'Calc Time: {t2-t1}')
    # Create Final FMM List
    fastMarchingStartPointListFMM = fmm_list_creation(fmmY,fmmX)
    print(fastMarchingStartPointListFMM)
    # Computing the local cost function
    print('Preparing to calculate cost function')
    curvatureDemArray = Curvature_Preparation(curvatureDemArray)

    # Calculate the local reciprocal cost (weight, or propagation speed in the
    # eikonal equation sense).  If the cost function isn't defined, default to
    # old cost function.
    print('Calculating local costs')
    reciprocalLocalCostArray = Local_Cost_Computation(flowArray, flowMean,
                                                      skeletonFromFlowAndCurvatureArray,
                                                      curvatureDemArray)
    del curvatureDemArray, skeletonFromFlowAndCurvatureArray
    # Compute the geodesic distance using Fast Marching Method
    geodesicDistanceArray = Fast_Marching(fastMarchingStartPointListFMM, basinIndexArray, flowArray, reciprocalLocalCostArray)
    
    


if __name__ == '__main__':
    t0 = perf_counter()
    main()
    t1 = perf_counter()
    print("time taken to complete cost computation and fast marching:",
    t1-t0, " seconds")



