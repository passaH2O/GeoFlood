#! /usr/bin/env python
# Set default parameters for GeoNet

# Setting up Geonet grass location
from __future__ import division
import shutil
import os
import pygeonet_prepare as Parameters


# Reporting, plotting and file handling
doFileOutput = 1
doReport = 1
doPlot = 1
doResetFiguresOnStart = 1


# **** Default Parameters for Perona-Malik nonlinear diffusion
# ... could be:  PeronaMalik1, PeronaMalik2, Tukey, rampPreserving

#diffusionMethod = 'PeronaMalik1'
diffusionMethod = 'PeronaMalik2'


diffusionTimeIncrement = 0.1  # this makes the explicit scheme stable
diffusionSigmaSquared = 0.05
nFilterIterations = 50 # Nonlinear filtering iterations

# Flow routing options and sub basin indexing
thresholdAreaSubBasinIndexing = 1500

# Define the cost function
# areaArray=D8 accumulation area
# flowArray=Dinf accumulation area
# slopeDemArray=local (scalar, modulus) slope
# curvatureDemArray=geometric curvature
# areaMean=mean D8 accumulation area
# flowMean=mean Dinf accumulation area
# skeletonFromFlowArray=skeleton based on Dinf flow
# skeletonFromCurvatureArray=skeleton based on curvature
# skeletonFromFlowAndCurvatureArray=skeleton based on Dinf flow and curvature
# reciprocalLocalCostFn='(flowArray.^(1/3.0)).*(slopeDemArray.^(-1/3.0))+20'
# reciprocalLocalCostFn = 'flowArray + '+\
# '30*skeletonFromFlowAndCurvatureArray + '+ \
# 'exp(curvatureDemArray*3)'
# doNormalizeCurvature = 0
reciprocalLocalCostFn = 'flowArray + ' + \
                        'flowMean*skeletonFromFlowAndCurvatureArray' + \
                        ' + flowMean*curvatureDemArray'
doNormalizeCurvature = 1
reciprocalLocalCostMinimum = 'nan'

# What proportion of the DEM should we track drainage?
thresholdPercentAreaForDelineation = 0.1
#demNanFlag = -9999  
#demErrorFlag = -9999  
demNanFlag = -3.402823e+038
demErrorFlag = -3.402823e+038


# The demSmoothingQuantile is the quantile of landscape we want to smooth and
# (1-demSmoothingQuantile) is the quantile of landscape we want to enhance.
# A good range of demSmoothingQuantile is 0.5 to 0.9
demSmoothingQuantile = 0.9
#curvatureCalcMethod = 'laplacian'
curvatureCalcMethod = 'geometric'
thresholdQqCurvature = 0
flowThresholdForSkeleton = 500
channelheadPredefined = 0

# Channel head search box size applied on skeleton image
endPointSearchBoxSize = 30
# Option used in discrete geodesic path finding from channel heads to outlets
doTrueGradientDescent = 1
