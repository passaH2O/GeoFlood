import numpy as np
import scipy.signal as conv2
from time import clock
from scipy.stats.mstats import mquantiles
from pygeonet_rasterio import *
from pygeonet_plot import *


# Gaussian Filter
def simple_gaussian_smoothing(inputDemArray, kernelWidth,
                              diffusionSigmaSquared):
    """
    smoothing input array with gaussian filter
    Code is vectorized for efficiency Harish Sangireddy
    """
    [Ny, Nx] = inputDemArray.shape
    halfKernelWidth = (kernelWidth-1)/2
    # Make a ramp array with 5 rows each containing [-2, -1, 0, 1, 2]
    x = np.linspace(-halfKernelWidth, halfKernelWidth, kernelWidth)
    y = x
    xv, yv = np.meshgrid(x, y)
    gaussianFilter = np.exp(-(
        xv**2+yv**2)/(2*diffusionSigmaSquared))  # 2D Gaussian
    gaussianFilter = gaussianFilter/np.sum(gaussianFilter[:])  # Normalize
    xL = np.nanmean(inputDemArray[:, 0:halfKernelWidth], axis=1)
    xR = np.nanmean(inputDemArray[:, Nx-halfKernelWidth:Nx], axis=1)
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
    return smoothedDemArray


def geonet_diffusion(demArray, diffusionMethod, nFilterIterations,
                     edgeThreshold, diffusionTimeIncrement,
                     diffusionSigmaSquared, pixelSize):
    """
    References:
       Based on diffusion() by Guy Gilboa
       Code imported from GeoNet2.1 by Harish Sangireddy June 2014
    """
    print 'Performing Perona Malik'
    print diffusionMethod, nFilterIterations, edgeThreshold,
    diffusionTimeIncrement, diffusionSigmaSquared, pixelSize
    # DTM dimensions
    [Ny, Nx] = demArray.shape
    print Ny, Nx
    for i in range(0, nFilterIterations):
        print "iteration", i
        # Gaussian filter the DTM using a 5x5 kernel (Catte et al)
        if diffusionSigmaSquared > 0:
            originalDemArray = demArray   # Save original DTM array
            demArrayout = simple_gaussian_smoothing(demArray, 5,
                                                    diffusionSigmaSquared)
        del demArray
        demArray = demArrayout
        # print 'demArray after gaussian smoothing',demArray.shape
        # Now calculate gradient in all directions (N,S,E,W) by simple
        # differencing - with repeat padding in each direction.
        # This step will propagate NaNs one pixel inward in each dirn.
        demArrayMatrix = np.matrix(demArray)
        In = (np.concatenate((demArrayMatrix[0, :], demArrayMatrix[0:Ny-1, :]),
                             0) - demArrayMatrix)/pixelSize
        # print In.shape
        # stop
        Is = (np.concatenate((demArrayMatrix[1:Ny, :],
                              demArrayMatrix[Ny-1, :]),
                             0) - demArrayMatrix)/pixelSize
        # print Isgr.shape, Is.shape
        # print np.nanmean(Isgr - Is)
        # stop
        Ie = (np.concatenate((demArrayMatrix[:, 1:Nx],
                              demArrayMatrix[:, Nx-1]),
                             1) - demArrayMatrix)/pixelSize
        # print Ie.shape

        Iw = (np.concatenate((demArrayMatrix[:, 0],
                              demArrayMatrix[:, 0:Nx-1]),
                             1) - demArrayMatrix)/pixelSize
        # print Iw.shape
        In[np.isnan(In)] = 0
        Is[np.isnan(Is)] = 0
        Ie[np.isnan(Ie)] = 0
        Iw[np.isnan(Iw)] = 0

        # Calculate diffusion coefficients in all dirns
        # according to diffusionMethod
        if diffusionMethod == 'linear':
            Cn = edgeThreshold
            Cs = edgeThreshold
            Ce = edgeThreshold
            Cw = edgeThreshold
        elif diffusionMethod == 'PeronaMalik1':
            Cn = np.exp(-(np.abs(In)/edgeThreshold)**2)
            Cs = np.exp(-(np.abs(Is)/edgeThreshold)**2)
            Ce = np.exp(-(np.abs(Ie)/edgeThreshold)**2)
            Cw = np.exp(-(np.abs(Iw)/edgeThreshold)**2)
        elif diffusionMethod == 'PeronaMalik2':
            Cn = 1/(1+np.array(np.abs(In)/edgeThreshold)**2)
            Cs = 1/(1+np.array(np.abs(Is)/edgeThreshold)**2)
            Ce = 1/(1+np.array(np.abs(Ie)/edgeThreshold)**2)
            Cw = 1/(1+np.array(np.abs(Iw)/edgeThreshold)**2)
        else:
            print 'Unknown smoothing method', diffusionMethod

        if diffusionSigmaSquared > 0:
            # Calculate real gradients (not smoothed) - with repeat padding
            # in each direction.
            # This step will propagate NaNs one pixel inward in each dirn.
            originalDemArrayMatrix = np.matrix(originalDemArray)
            In = (np.concatenate((originalDemArrayMatrix[0, :],
                                  originalDemArrayMatrix[0:Ny-1, :]),
                                 0) - originalDemArrayMatrix)/pixelSize
            Is = (np.concatenate((originalDemArrayMatrix[1:Ny, :],
                                  originalDemArrayMatrix[Ny-1, :]),
                                 0) - originalDemArrayMatrix)/pixelSize
            Ie = (np.concatenate((originalDemArrayMatrix[:, 1:Nx],
                                  originalDemArrayMatrix[:, Nx-1]),
                                 1) - originalDemArrayMatrix)/pixelSize
            Iw = (np.concatenate((originalDemArrayMatrix[:0],
                                  originalDemArrayMatrix[:, 0:Nx-1]),
                                 1) - originalDemArrayMatrix)/pixelSize
            In[np.isnan(In)] = 0
            Is[np.isnan(Is)] = 0
            Ie[np.isnan(Ie)] = 0
            Iw[np.isnan(Iw)] = 0
            demArray = originalDemArray

        part6 = (np.array(Cn)*np.array(In) + np.array(Cs)*np.array(Is) +
                 np.array(Ce)*np.array(In) + np.array(Cw)*np.array(Iw))
        demArrayMatrix = demArrayMatrix + diffusionTimeIncrement*(part6)

    return np.array(demArrayMatrix)


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
    for ii in xrange(niter):

        # calculate the diffs
        deltaS[:-1, :] = np.diff(imgout, axis=0)
        deltaE[:, :-1] = np.diff(imgout, axis=1)
        if option == 2:
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
    print 'Computing slope of raw DTM'
    slopeXArray, slopeYArray = np.gradient(nanDemArray,
                                           Parameters.demPixelScale)
    slopeMagnitudeDemArray = np.sqrt(slopeXArray**2 + slopeYArray**2)
    print 'DEM slope array shape:', slopeMagnitudeDemArray.shape
    # plot the slope DEM array
    if defaults.doPlot == 1:
        raster_plot(slopeMagnitudeDemArray, 'Slope of unfiltered DEM')
    # Computation of the threshold lambda used in Perona-Malik nonlinear
    # filtering. The value of lambda (=edgeThresholdValue) is given by the 90th
    # quantile of the absolute value of the gradient.
    print'Computing lambda = q-q-based nonlinear filtering threshold'
    slopeMagnitudeDemArray = slopeMagnitudeDemArray.flatten()
    slopeMagnitudeDemArray = slopeMagnitudeDemArray[~np.isnan(
        slopeMagnitudeDemArray)]
    print 'dem smoothing Quantile', defaults.demSmoothingQuantile
    edgeThresholdValue = np.asscalar(mquantiles(
        np.absolute(slopeMagnitudeDemArray),
        defaults.demSmoothingQuantile))
    print 'edgeThresholdValue:', edgeThresholdValue
    return edgeThresholdValue


def main():
    nanDemArray = read_dem_from_geotiff(Parameters.demFileName,
                                        Parameters.demDataFilePath)
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
        print defaults.diffusionMethod+" filter is not available in the"
        "current version GeoNet"
    # plotting the filtered DEM
    if defaults.doPlot == 1:
        raster_plot(filteredDemArray, 'Filtered DEM')
    # Writing the filtered DEM as a tif
    write_geotif_filteredDEM(filteredDemArray, Parameters.demDataFilePath,
                             Parameters.demFileName)
#     # performing Perona-Malik filtering
#     print 'Performing Perona-Malik nonlinear filtering'
#     filteredDemArray = geonet_diffusion (nanDemArray,\
#     defaults.diffusionMethod,\
#     defaults.nFilterIterations, edgeThresholdValuescipy,\
#     defaults.diffusionTimeIncrement,\
#     defaults.diffusionSigmaSquared, 1+0*Parameters.demPixelScale)


if __name__ == '__main__':
    t0 = clock()
    main()
    t1 = clock()
    print "time taken to complete nonlinear filtering:", t1-t0, " seconds"
