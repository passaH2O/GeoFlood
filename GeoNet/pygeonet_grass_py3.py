from __future__ import division
import os
import sys
import shutil
import subprocess
from time import perf_counter 
from pygeonet_rasterio import *


def grass(filteredDemArray):

    # Software
    if sys.platform.startswith('win'):
        # MS Windows
        grass7bin = r'C:\OSGeo4W64\bin\grass78.bat'
        # uncomment when using standalone WinGRASS installer
        # grass7bin = r'C:\Program Files (x86)\GRASS GIS 7.2.0\grass72.bat'
        # this can be avoided if GRASS executable is added to PATH
    elif sys.platform.startswith('darwin'):
        # Mac OS X
        # TODO: this have to be checked, maybe unix way is good enough
        grass7bin = '/Applications/GRASS/GRASS-7.8.app/'
    elif sys.platform.startswith('linux'):
        grass7bin = r'grass78'
    else:
        raise OSError('Platform not configured')
    
    # Query GRASS 7 itself for its GISBASE
    startcmd = [grass7bin, '--config', 'path']

    p = subprocess.Popen(startcmd, shell=True,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    if p.returncode != 0:
        print('ERROR: %s' % err, file=sys.stderr)
        print("ERROR: Cannot find GRASS GIS 7 " \
              "start script (%s)" % startcmd, file=sys.stderr)
        sys.exit(-1)

    if sys.platform.startswith('linux'):
        gisbase = out.decode("utf-8").strip('\n')
    elif sys.platform.startswith('win'):
        if out.decode("utf-8").find("OSGEO4W home is") != -1:
            gisbase = out.decode("utf-8").strip().split('\r\n')[1]
        else:
            gisbase = out.decode("utf-8").strip('\r\n')
        os.environ['GRASS_SH'] = os.path.join(gisbase, 'mysys', 'bin', 'sh.exe')
    else:
        gisbase = out.decode("utf-8").strip('\n\r')

    # Set environment variables
    os.environ['GISBASE'] = gisbase
    os.environ['PATH'] += os.pathsep + os.path.join(gisbase, 'extrabin')
    # add path to GRASS addons
    home = os.path.expanduser("~")
    os.environ['PATH'] += os.pathsep + os.path.join(home, '.grass7', 'addons', 'scripts')

    # Define GRASS-Python environment
    gpydir = os.path.join(gisbase, "etc", "python")
    sys.path.append(gpydir)

    # Set GISDBASE environment variable
    if sys.platform.startswith('win'):
        gisdb = os.path.join(home, "Documents", "grassdata")
    else:
        gisdb = os.path.join(home, "grassdata")
    os.environ['GISDBASE'] = gisdb
    # Make GRASS GIS Database if doesn't already exist
    if not os.path.exists(gisdb):
        try:
            os.makedirs(gisdb)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

    # Linux: Set path to GRASS libs
    path = os.getenv('LD_LIBRARY_PATH')
    directory = os.path.join(gisbase, 'lib')
    if path:
        path = directory + os.pathsep + path
    else:
        path = directory
    os.environ['LD_LIBRARY_PATH'] = path

    # Language
    os.environ['LANG'] = 'en_US'
    os.environ['LOCALE'] = 'C'

    # Location
    location = 'geonet'
    os.environ['LOCATION_NAME'] = location
    grassGISlocation = os.path.join(gisdb, location)
    if os.path.exists(grassGISlocation):
        print("Cleaning existing Grass location")
        shutil.rmtree(grassGISlocation)

    mapset = 'PERMANENT'
    os.environ['MAPSET'] = mapset

    # import GRASS Python bindings
    import grass.script as g
    import grass.script.setup as gsetup

    # Launch session
    gsetup.init(gisbase, gisdb, location, mapset)

    #originalGeotiff = os.path.join(Parameters.demDataFilePath, Parameters.demFileName)
    geotiff = Parameters.pmGrassGISfileName
    print('Making the geonet location')
    g.run_command('g.proj', georef=geotiff, location = location)
    print('Existing Mapsets after making locations:')
    g.read_command('g.mapsets', flags = 'l')
    print('Setting GRASSGIS environ')
    gsetup.init(gisbase, gisdb, location, mapset)
    ##    g.gisenv()

    # Mapset
    mapset = 'geonetuser'
    os.environ['MAPSET'] = mapset
    print('Making mapset now')
    g.run_command('g.mapset', flags = 'c', mapset = mapset,\
                  location = location, dbase = gisdb)
    # gsetup initialization 
    gsetup.init(gisbase, gisdb, location, mapset)

    # Manage extensions
    extensions = ['r.stream.basins', 'r.stream.watersheds']
    extensions_installed = g.read_command('g.extension', 'a').splitlines()
    for extension in extensions:
        if extension in extensions_installed:
            g.run_command('g.extension', extension=extension, operation="remove")
            g.run_command('g.extension', extension=extension)
        else:
            g.run_command('g.extension', extension=extension)
            
    # Read the filtered DEM
    print('Import filtered DEM into GRASSGIS and '\
          'name the new layer with the DEM name')
    demFileName = Parameters.demFileName # this reads something like skunk.tif
    geotiffmapraster = demFileName.split('.')[0]
    print('GRASSGIS layer name: ',geotiffmapraster)
    g.run_command('r.in.gdal', input=geotiff, \
                  output=geotiffmapraster,overwrite=True)
    gtf = Parameters.geotransform
    #Flow computation for massive grids (float version)
    print("Calling the r.watershed command from GRASS GIS")
    subbasinThreshold = defaults.thresholdAreaSubBasinIndexing
    if (not hasattr(Parameters, 'xDemSize')) or (not hasattr(Parameters, 'yDemSize')):
        Parameters.yDemSize=np.size(filteredDemArray,0)
        Parameters.xDemSize=np.size(filteredDemArray,1)
    if Parameters.xDemSize > 4000 or Parameters.yDemSize > 4000:
        print ('using swap memory option for large size DEM')
        g.run_command('r.watershed',flags ='am',overwrite=True,\
                      elevation=geotiffmapraster, \
                      threshold=subbasinThreshold, \
                      drainage = 'dra1v23')
        g.run_command('r.watershed',flags ='am',overwrite=True,\
                      elevation=geotiffmapraster, \
                      threshold=subbasinThreshold, \
                      accumulation='acc1v23')
    else :
        g.run_command('r.watershed',flags ='a',overwrite=True,\
                      elevation=geotiffmapraster, \
                      threshold=subbasinThreshold, \
                      accumulation='acc1v23',\
                      drainage = 'dra1v23')
    print('Identify outlets by negative flow direction')
    g.run_command('r.mapcalc',overwrite=True,\
                  expression='outletmap = if(dra1v23 >= 0,null(),1)')
    print('Convert outlet raster to vector')
    g.run_command('r.to.vect',overwrite=True,\
                  input = 'outletmap', output = 'outletsmapvec',\
                  type='point')
    print('Delineate basins according to outlets')
    g.run_command('r.stream.basins',overwrite=True,\
                  direction='dra1v23',points='outletsmapvec',\
                  basins = 'outletbasins')
    # Save the outputs as TIFs
    outlet_filename = geotiffmapraster + '_outlets.tif'
    g.run_command('r.out.gdal',overwrite=True,\
                  input='outletmap', type='Float32',\
                  output=os.path.join(Parameters.geonetResultsDir,
                                      outlet_filename),\
                  format='GTiff')
    outputFAC_filename = geotiffmapraster + '_fac.tif'
    g.run_command('r.out.gdal',overwrite=True,\
                  input='acc1v23', type='Float64',\
                  output=os.path.join(Parameters.geonetResultsDir,
                                      outputFAC_filename),\
                  format='GTiff')
    outputFDR_filename = geotiffmapraster + '_fdr.tif'
    g.run_command('r.out.gdal',overwrite=True,\
                  input = "dra1v23", type='Int32',\
                  output=os.path.join(Parameters.geonetResultsDir,
                                      outputFDR_filename),\
                  format='GTiff')
    outputBAS_filename = geotiffmapraster + '_basins.tif'
    g.run_command('r.out.gdal',overwrite=True,\
                  input = "outletbasins", type='Int16',\
                  output=os.path.join(Parameters.geonetResultsDir,
                                      outputBAS_filename),\
                  format='GTiff')

def main():
    filteredDemArray = read_geotif_filteredDEM()
    grass(filteredDemArray)

if __name__ == '__main__':
    t0 = perf_counter()
    main()
    t1 = perf_counter()
    print(("time taken to complete flow accumulation:", t1-t0, " seconds"))
    sys.exit(0)
