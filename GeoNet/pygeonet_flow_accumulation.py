from __future__ import division
import os
import sys
import shutil
from time import perf_counter 
import subprocess
from pygeonet_rasterio import *
from pygeonet_plot import *


# Flow accumulation is computed by calling GRASS GIS functions.
def flowaccumulation(filteredDemArray):
    # Most of the processing here is commented out until GRASS is available for Python3.
    # When available, uncomment the lines with a single #
    #grass7bin = 'grass76'
    #if sys.platform.startswith('win'):
    #    # MS Windows
    #    grass7bin = r'C:\Program Files\GRASS GIS 7.6\grass76.bat'
    #    # uncomment when using standalone WinGRASS installer
    #    # grass7bin = r'C:\Program Files (x86)\GRASS GIS 7.2.0\grass72.bat'
    #    # this can be avoided if GRASS executable is added to PATH
    #elif sys.platform == 'darwin':
    #    # Mac OS X
    #    # TODO: this has to be checked, maybe unix way is good enough
    #    grass7bin = '/Applications/GRASS/GRASS-7.6.app/'
    #mswin = sys.platform.startswith('win')
    #if mswin:
    #    gisdbdir = os.path.join(os.path.expanduser("~"), "Documents\grassdata")
    #else:
    #    gisdbdir = os.path.join(os.path.expanduser("~"), "grassdata")
    #locationGeonet = 'geonet'
    #mapsetGeonet = 'geonetuser'
    #if sys.platform.startswith("win"):
    #    import ctypes
    #    SEM_NOGPFAULTERRORBOX = 0x0002  # From MSDN
    #    ctypes.windll.kernel32.SetErrorMode(SEM_NOGPFAULTERRORBOX)
    #    CREATE_NO_WINDOW = 0x08000000    # From Windows API
    #    subprocess_flags = CREATE_NO_WINDOW
    #else:
    #    subprocess_flags = 0
    #subprocess_flags = 0
    #startcmd = [grass7bin, os.path.join(gisdbdir, locationGeonet,
    #                                    mapsetGeonet), '--exec',
    #            os.path.join(Parameters.geoNetHomeDir,
    #                         "GeoNet","pygeonet_grass.py")]
##  #  startcmd = ['python', os.path.join(os.path.dirname(__file__),
##  #                                     "pygeonet_grass.py")]
    #p = subprocess.Popen(startcmd, shell=True,
    #                     stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    #                     creationflags=subprocess_flags)
    #out, err = p.communicate()
    #print(out, err)
    tmpfile = Parameters.demFileName  # this reads the name of the DEM
    geotiffmapraster = tmpfile.split('.')[0]
    print('GRASSGIS layer name: ', geotiffmapraster)
    gtf = Parameters.geotransform
    # Save the outputs as TIFs
    outlet_filename = geotiffmapraster + '_outlets.tif'
    outputFAC_filename = geotiffmapraster + '_fac.tif'
    outputFDR_filename = geotiffmapraster + '_fdr.tif'
    outputBAS_filename = geotiffmapraster + '_basins.tif'
    ## plot the flow directions
    nanDemArrayfdr = read_geotif_generic(Parameters.geonetResultsDir,
                                         outputFDR_filename)
    if defaults.doPlot == 1:
        raster_plot(nanDemArrayfdr, 'Flow directions DEM')
    """
    Output drainage raster map contains drainage direction.
    Provides the "aspect" for each cell measured CCW from East.
    Multiplying positive values by 45 will give the direction
    in degrees that the surface runoff will travel from that cell.
    The value 0 (zero) indicates that the cell is a depression area
    (defined by the depression input map).

    Negative values indicate that surface runoff is leaving the boundaries
    of the current geographic region. The absolute value of these
    negative cells indicates the direction of flow.
    """
    outlets = np.where(nanDemArrayfdr < 0)
    print("Number of outlets :", str(len(outlets[0])))
    # print ([[outlets[0][i], outlets[1][i]] for i in range(len(outlets[0]))])
    # plot the flow accumulation
    nanDemArrayfac = read_geotif_generic(Parameters.geonetResultsDir,
                                         outputFAC_filename)
    if defaults.doPlot == 1:
        raster_plot(nanDemArrayfac, 'Flow accumulations DEM')
    # getting the bigbasins from the r.streams.basins modules
    nanDemArraybasins = read_geotif_generic(Parameters.geonetResultsDir,
                                            outputBAS_filename)
    nanDemArraybasins[np.isnan(filteredDemArray)] = 0
    # write outlet info into a csv file
    outlet_tablename = geotiffmapraster + '_outlets.csv'
    outlet_tablelocation = os.path.join(Parameters.geonetResultsDir,
                                        outlet_tablename)
    if os.path.exists(outlet_tablelocation):
        os.remove(outlet_tablelocation)
    with open(outlet_tablelocation, 'a') as f:
        f.write('BasinID,YIndex,XIndex\n')
        for i in range(len(outlets[0])):
            f.write(str(nanDemArraybasins[outlets[0][i], outlets[1][i]]) +
                    ',' + str(outlets[0][i]) + ',' + str(outlets[1][i]) + '\n')
    # outlets locations in projection of the input dataset
    outletsxx = outlets[1]
    outletsxxfloat = [float(x)+0.5 for x in outletsxx]
    outletsyy = outlets[0]
    outletsyyfloat = [float(x)+0.5 for x in outletsyy]
    """
    outletsxxProj = np.array(outletsxxfloat) * Parameters.demPixelScale + \
                    Parameters.xLowerLeftCoord + float(0.0164)
    outletsyyProj = Parameters.yLowerLeftCoord - np.array(outletsyyfloat) * \
                    Parameters.demPixelScale + \
                    Parameters.yDemSize * Parameters.demPixelScale + \
                    float(0.0155)
    # The extra decimal digits is essentially a hack into
    # Grass GIS r.water.outlet routine, which only, works
    # with atleast 4 significant digits
    """
    outletsxxProj = (float(gtf[0]) +
                     float(gtf[1]) * np.array(outletsxxfloat))
    outletsyyProj = (float(gtf[3]) +
                     float(gtf[5]) * np.array(outletsyyfloat))
    # plotting log10 flow accumulation with outlets
    drainageMeasure = np.log10(nanDemArrayfac)
    if defaults.doPlot == 1:
        raster_point_plot(drainageMeasure, outlets, 'flowArray with outlets')
    # plotting subbasins with outlets
    if defaults.doPlot == 1:
        raster_point_plot(nanDemArraybasins, outlets,
                          'basinIndexArray with outlets', cm.Dark2)
    return {'outlets': outlets, 'fac': nanDemArrayfac,
            'fdr': nanDemArrayfdr,
            'outletsxxProj': outletsxxProj, 'outletsyyProj': outletsyyProj,
            'bigbasins': nanDemArraybasins}
    # end of flow accumulation


def main():
    print(Parameters.pmGrassGISfileName)
    filteredDemArray = read_geotif_filteredDEM()
    flowroutingresults = flowaccumulation(filteredDemArray)

if __name__ == '__main__':
    t0 = perf_counter()
    main()
    t1 = perf_counter()
    print(("time taken to complete flow accumulation:", t1-t0, " seconds"))
