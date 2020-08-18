from __future__ import division
import numpy as np
import rasterio
from rasterio import features
from time import perf_counter 
from pygeonet_rasterio import *
from pygeonet_plot import *

# Skeleton by thresholding one grid measure e.g. flow or curvature
def compute_skeleton_by_single_threshold(inputArray, threshold):
    skeletonArray = np.zeros((inputArray.shape))
    np.warnings.filterwarnings('ignore')
    skeletonArray[np.where(inputArray > threshold)] = 1
    return skeletonArray


# Skeleton by thresholding two grid measures e.g. flow and curvature
def compute_skeleton_by_dual_threshold(inputArray1,
                                       inputArray2,
                                       threshold1,
                                       threshold2):
    skeletonArray = np.zeros((inputArray1.shape))
    mask1 = np.where(inputArray1 > threshold1, 1, False)
    mask2 = np.where(inputArray2 > threshold2, 1, False)
    skeletonArray = mask1 * mask2
    return skeletonArray


def main():
    outfilepath = Parameters.geonetResultsDir
    inputfilepath = Parameters.demDataFilePath
    demName = Parameters.demFileName
    curvature_filename = demName.split('.')[0] + '_curvature.tif'
    fac_filename = demName.split('.')[0] + '_fac.tif'
    thresholdCurvatureQQxx = 1.5
#     outlets = [[2, 4, 9], [27, 26, 23]]
    filteredDemArray = read_geotif_filteredDEM()
    curvatureDemArray,prj_curv,src_curv = read_geotif_generic(outfilepath, curvature_filename)
    finiteCurvatureDemList = curvatureDemArray[np.isfinite(
        curvatureDemArray[:])]
    curvatureDemMean = np.nanmean(finiteCurvatureDemList)
    curvatureDemStdDevn = np.nanstd(finiteCurvatureDemList)
    print('Curvature mean: ', curvatureDemMean)
    print('Curvature standard deviation: ', curvatureDemStdDevn)
    print(f'DEM Projection: {prj_curv}')
    flowArray,prj_fac,src_fac = read_geotif_generic(outfilepath, fac_filename)
    flowArray[np.isnan(filteredDemArray)] = np.nan
    flowMean = np.mean(flowArray[~np.isnan(flowArray[:])])
    
    print('Mean upstream flow: ', flowMean)
    del filteredDemArray

    # Define a skeleton based on flow alone
    skeletonFromFlowArray = \
    compute_skeleton_by_single_threshold(flowArray,
                                         defaults.flowThresholdForSkeleton)

    
    # Define a skeleton based on curvature alone
    skeletonFromCurvatureArray = \
    compute_skeleton_by_single_threshold(curvatureDemArray,
                                         curvatureDemMean +
                                         thresholdCurvatureQQxx *
                                         curvatureDemStdDevn)

    
    # Writing the skeletonFromCurvatureArray array
    outfilename = demName.split('.')[0]+'_curvatureskeleton.tif'
    write_geotif_generic(skeletonFromCurvatureArray,
                         outfilepath, outfilename)
    del skeletonFromCurvatureArray

    # Writing the skeletonFromFlowArray array
    outfilename = demName.split('.')[0]+'_flowskeleton.tif'
    write_geotif_generic(skeletonFromFlowArray,
                         outfilepath, outfilename)
    
    # Define a skeleton based on curvature and flow
    skeletonFromFlowAndCurvatureArray = \
    compute_skeleton_by_dual_threshold(curvatureDemArray, flowArray,
                                       curvatureDemMean +
                                       thresholdCurvatureQQxx *
                                       curvatureDemStdDevn,
                                       defaults.flowThresholdForSkeleton)
    del flowArray
    del curvatureDemArray

    # Writing the skeletonFromFlowAndCurvatureArray array
    outfilename = demName.split('.')[0] + '_skeleton.tif'
    write_geotif_generic(skeletonFromFlowAndCurvatureArray,
                         outfilepath, outfilename)
    del skeletonFromFlowAndCurvatureArray


    # plotting only for testing purposes
    #try:
    #    if defaults.doPlot == 1:
    #        raster_point_plot(skeletonFromFlowAndCurvatureArray, outlets,
    #                          'Skeleton with outlets', cm.binary)
    #except NameError:
    #    pass
    
        
if __name__ == '__main__':
    t0 = perf_counter()
    main()
    t1 = perf_counter()
    print(("time taken to complete skeleton definition:", t1-t0, " seconds"))

