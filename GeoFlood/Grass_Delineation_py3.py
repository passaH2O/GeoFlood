from __future__ import division
import os
import sys
import shutil
import subprocess
from time import perf_counter 
import configparser
import inspect
from GeoFlood_Filename_Finder import cfg_finder


def segment_catchment_delineation(fdrfn, segshp, segcatfn):

    # Software
    if sys.platform.startswith('win'):
        # MS Windows
        # grass7bin = r'C:\Program Files\GRASS GIS 7.2.1\grass72.bat'
        grass7bin = r'C:\OSGeo4W64\bin\grass78.bat'
        # uncomment when using standalone WinGRASS installer
        # grass7bin = r'C:\Program Files (x86)\GRASS GIS 7.2.0\grass72.bat'
        # this can be avoided if GRASS executable is added to PATH
    elif sys.platform.startswith('darwin'):
        # Mac OS X
        grass7bin = '/Applications/GRASS-8.3.app/Contents/Resources/bin/grass'
    elif sys.platform.startswith('linux'):
        # grass7bin = 'grass78'
        grass7bin = 'grass'
    else:
        raise OSError('Platform not configured.')

    # Query GRASS 7 itself for its GISBASE
    startcmd = [grass7bin, '--config', 'path']
    p = subprocess.Popen(startcmd, shell=False,
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
    # os.environ['PATH'] += os.pathsep + os.path.join(home, '.grass8', 'addons', 'scripts')

    # Definte GRASS-Python environment
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

    # Linux: set path to GRASS libs
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
    # if os.path.exists(grassGISlocation):
    #     print("Cleaning existing Grass location")
    #     shutil.rmtree(grassGISlocation)

    # Mapset
    mapset = 'PERMANENT'
    os.environ['MAPSET'] = mapset

    # Import GRASS Python bindings
    import grass.script as g
    import grass.script.setup as gsetup

    # Launch session
    gsetup.init(gisdb, location, mapset)

    # print('Making the geonet location')
    # g.run_command('g.proj', georef=fdrfn, location = location)
    print('Existing Mapsets after making locations:')
    g.read_command('g.mapsets', flags = 'l')
    print('Setting GRASSGIS environ')
    gsetup.init(gisdb, location, mapset)
    ##    g.gisenv()

    # Mapset
    mapset = 'geonetuser'
    os.environ['MAPSET'] = mapset
    print('Making mapset now')
    g.run_command('g.mapset', flags = 'c', mapset = mapset,\
                  location = location, dbase = gisdb)
    # gsetup initialization 
    gsetup.init(gisdb, location, mapset)
    
    # Manage extensions
    extensions = ['r.stream.basins', 'r.stream.watersheds']
    extensions_installed = g.read_command('g.extension', 'a').splitlines()
    for extension in extensions:
        if extension in extensions_installed:
            g.run_command('g.extension', extension=extension, operation="remove")
        g.run_command(
            'g.extension', extension=extension,
            url='https://svn.osgeo.org/grass/grass-addons/grass7')

    # Read the flow direction raster
    g.run_command('r.in.gdal', input=fdrfn,
                  output='fdr',overwrite=True)
    g.run_command('g.region', raster='fdr')
    # Read the channel segment shapefile
    g.run_command('v.in.ogr', input=segshp,
                  output='Segment')
    g.run_command('v.to.rast', input='Segment', use='attr',
                  output='stream', attribute_column='HYDROID')
    g.run_command('r.stream.basins',overwrite=True,\
                  direction='fdr',stream_rast='stream',\
                  basins = 'subbasins')
    g.run_command('r.out.gdal',overwrite=True,
                  input='subbasins', type='Int16',
                  output=segcatfn,
                  format='GTiff')

def main():
    geofloodHomeDir,projectName,DEM_name,chunk_status,input_fn,output_fn,hr_status = cfg_finder()
    geofloodResultsDir = os.path.join(geofloodHomeDir, output_fn,
                                   "GIS", projectName)
    Name_path = os.path.join(geofloodResultsDir, DEM_name)
    fdrfn = Name_path + '_fdr.tif'
    segshp = Name_path+ "_channelSegment.shp"
    segcatfn = Name_path + '_segmentCatchment.tif'
    segment_catchment_delineation(fdrfn, segshp, segcatfn)

if __name__ == '__main__':
    t0 = perf_counter()
    main()
    t1 = perf_counter()
    print("time taken to complete delineation:",t1-t0," seconds")
    sys.exit(0)
