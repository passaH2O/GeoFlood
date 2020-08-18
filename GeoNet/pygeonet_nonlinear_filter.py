from __future__ import division
import numpy as np
import scipy.signal as conv2
from time import perf_counter 
from scipy.stats.mstats import mquantiles
from pygeonet_rasterio import *
from pygeonet_plot import *
from numba import njit

# Gaussian Filter
def simple_gaussian_smoothing(inputDemArray, kernelWidth,
                              diffusionSigmaSquared):
    """
    smoothing input array with gaussian filter
    Code is vectorized for efficiency Harish Sangireddy
    """
    [Ny, Nx] = inputDemArray.shape
    halfKernelWidth = int((kernelWidth-1)/2)
    # Make a ramp array with 5 rows each containing [-2, -1, 0, 1, 2]
    x = np.linspace(-halfKernelWidth, halfKernelWidth, kernelWidth)
    y = x
    xv, yv = np.meshgrid(x, y)
    gaussianFilter = np.exp(-(
        xv**2+yv**2)/(2*diffusionSigmaSquared))  # 2D Gaussian
    gaussianFilter = gaussianFilter/np.sum(gaussianFilter[:])  # Normalize
    print(inputDemArray[0, 0:halfKernelWidth])
    xL = np.nanmean(inputDemArray[:, 0:halfKernelWidth], axis=1)
    print(f'xL: {xL}')
    xR = np.nanmean(inputDemArray[:, Nx-halfKernelWidth:Nx], axis=1)
    print(f'xR: {xR}')
    part1T = np.vstack((xL, xL))
    part1 = part1T.T
    part2T = np.vstack((xR, xR))
    part2 = part2T.T
    eI = np.hstack((part1, inputDemArray, part2))
    xU = np.nanmean(eI[0:halfKernelWidth, :], axis=0)
    xD = np.nanmean(eI[Ny-halfKernelWidth:Ny, :], axis=0)
    part3 = np.vstack((xU, xU))
    part4 = np.vstack((xD, xD))
    # Generate the expanded DTM array, 4 pixels wider in both x,y directions
    eI = np.vstack((part3, eI, part4))
    # The 'valid' option forces the 2d convolution to clip 2 pixels off
    # the edges NaNs spread from one pixel to a 5x5 set centered on
    # the NaN
    fillvalue = np.nanmean(inputDemArray[:])
    smoothedDemArray = conv2.convolve2d(eI, gaussianFilter, 'valid')
    del inputDemArray, eI
    return smoothedDemArray

def anisodiff(img, niter, kappa, gamma, step=(1., 1.), option=2):
    # initialize output array
    img = img.astype('float32')
    imgout = img.copy()

    # initialize some internal variables
    deltaS = np.zeros_like(imgout)
    deltaE = deltaS.copy()
    NS = deltaS.copy()
    EW = deltaS.copy()
    gS = np.ones_like(imgout)
    gE = gS.copy()
    step1 = step[0]
    step2 = step[1]
    for ii in range(niter):

        # calculate the diffs
        deltaS[:-1, :] = np.diff(imgout, axis=0)
        deltaE[:, :-1] = np.diff(imgout, axis=1)
        if option == 2:
            #gS = gs_diff(deltaS,kappa,step1)
            #gE = ge_diff(deltaE,kappa,step2)
            gS = 1./(1.+(deltaS/kappa)**2.)/step[0]
            gE = 1./(1.+(deltaE/kappa)**2.)/step[1]
        elif option == 1:
            gS = np.exp(-(deltaS/kappa)**2.)/step[0]
            gE = np.exp(-(deltaE/kappa)**2.)/step[1]
        # update matrices
        E = gE*deltaE
        S = gS*deltaS
        # subtract a copy that has been shifted 'North/West' by one
        # pixel. don't ask questions. just do it. trust me.
        NS[:] = S
        EW[:] = E
        NS[1:, :] -= S[:-1, :]
        EW[:, 1:] -= E[:, :-1]
        # update the image
        mNS = np.isnan(NS)
        mEW = np.isnan(EW)
        NS[mNS] = 0
        EW[mEW] = 0
        NS += EW
        mNS &= mEW
        NS[mNS] = np.nan
        imgout += gamma*NS
    return imgout


def lambda_nonlinear_filter(nanDemArray):
    print ('Computing slope of raw DTM')
    slopeXArray, slopeYArray = np.gradient(nanDemArray,
                                           Parameters.demPixelScale)
    slopeMagnitudeDemArray = np.sqrt(slopeXArray**2 + slopeYArray**2)
    print(('DEM slope array shape:'), slopeMagnitudeDemArray.shape)
    
    # plot the slope DEM array
    #if defaults.doPlot == 1:
    #    raster_plot(slopeMagnitudeDemArray, 'Slope of unfiltered DEM')
    
    # Computation of the threshold lambda used in Perona-Malik nonlinear
    # filtering. The value of lambda (=edgeThresholdValue) is given by the 90th
    # quantile of the absolute value of the gradient.

    print ('Computing lambda = q-q-based nonlinear filtering threshold')
    slopeMagnitudeDemArray = slopeMagnitudeDemArray.flatten()
    slopeMagnitudeDemArray = slopeMagnitudeDemArray[~np.isnan(
        slopeMagnitudeDemArray)]
    print(('dem smoothing Quantile', defaults.demSmoothingQuantile))
    edgeThresholdValue = (mquantiles(
        np.absolute(slopeMagnitudeDemArray),
        defaults.demSmoothingQuantile)).item()
    print(('edgeThresholdValue:', edgeThresholdValue))
    return edgeThresholdValue


def main():
    nanDemArray = read_dem_from_geotiff(Parameters.demFileName,
                                        Parameters.demDataFilePath)
    print(np.max(nanDemArray))
    print(np.min(nanDemArray))
    nanDemArray[nanDemArray < defaults.demNanFlag] = np.nan
    if defaults.diffusionMethod == 'PeronaMalik2':
        edgeThresholdValue = lambda_nonlinear_filter(nanDemArray)
        filteredDemArray = anisodiff(nanDemArray, defaults.nFilterIterations,
                                     edgeThresholdValue,
                                     defaults.diffusionTimeIncrement,
                                     (Parameters.demPixelScale,
                                      Parameters.demPixelScale), 2)
    elif defaults.diffusionMethod == 'PeronaMalik1':
        edgeThresholdValue = lambda_nonlinear_filter(nanDemArray)
        filteredDemArray = anisodiff(nanDemArray, defaults.nFilterIterations,
                                     edgeThresholdValue,
                                     defaults.diffusionTimeIncrement,
                                     (Parameters.demPixelScale,
                                      Parameters.demPixelScale), 1)

    else:
        print((defaults.diffusionMethod+" filter is not available in the"))
        "current version GeoNet"   
    # plot the filtered DEM
    #if defaults.doPlot == 1:
    #    raster_plot(filteredDemArray, 'Filtered DEM')
        
    # Writing the filtered DEM as a tif
    write_geotif_filteredDEM(filteredDemArray, Parameters.demDataFilePath,
                             Parameters.demFileName)

if __name__ == '__main__':
    t0 = perf_counter()
    main()
    t1 = perf_counter()
    print(("time taken to complete nonlinear filtering:", t1-t0, " seconds"))
