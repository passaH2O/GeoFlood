import os
import sys
import shutil
import subprocess
from time import clock
import ConfigParser
import inspect
import grass.script as g
import grass.script.setup as gsetup


def segment_catchment_delineation(fdrfn, segshp, segcatfn):
    grass7bin = 'grass74'
    # grass7bin = 'grass72'
    if sys.platform.startswith('win'):
        # MS Windows
        # grass7bin = r'C:\Program Files\GRASS GIS 7.2.1\grass72.bat'
        grass7bin = r'C:\Program Files (x86)\GRASS GIS 7.4.0\grass74.bat'
        # uncomment when using standalone WinGRASS installer
        # grass7bin = r'C:\Program Files (x86)\GRASS GIS 7.2.0\grass72.bat'
        # this can be avoided if GRASS executable is added to PATH
    elif sys.platform == 'darwin':
        # Mac OS X
        # TODO: this have to be checked, maybe unix way is good enough
        grass7bin = '/Applications/GRASS/GRASS-7.2.app/'
    startcmd = [grass7bin, '--config', 'path']
    p = subprocess.Popen(startcmd, shell=False,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    if p.returncode != 0:
        print >>sys.stderr, "ERROR: Cannot find GRASS GIS 7 " \
              "start script (%s)" % startcmd
        sys.exit(-1)
    gisbase = out.strip('\n\r')
    gisdb = os.path.join(os.path.expanduser("~"), "grassdata")
    mswin = sys.platform.startswith('win')
    if mswin:
        gisdbdir = os.path.join(os.path.expanduser("~"), "Documents\grassdata")
    else:
        gisdbdir = os.path.join(os.path.expanduser("~"), "grassdata")
    locationGeonet = 'geonet'
    grassGISlocation = os.path.join(gisdbdir, locationGeonet)
    if os.path.exists(grassGISlocation):
        print "Cleaning existing Grass location"
        shutil.rmtree(grassGISlocation)
    gsetup.init(gisbase, gisdbdir, locationGeonet, 'PERMANENT')
    mapsetGeonet = 'geonetuser'
    print 'Making the geonet location'
    g.run_command('g.proj', georef=fdrfn, location = locationGeonet)
    location = locationGeonet 
    mapset = mapsetGeonet
    print 'Existing Mapsets after making locations:'
    g.read_command('g.mapsets', flags = 'l')
    print 'Setting GRASSGIS environ'
    gsetup.init(gisbase, gisdbdir, locationGeonet, 'PERMANENT')
    ##    g.gisenv()
    print 'Making mapset now'
    g.run_command('g.mapset', flags = 'c', mapset = mapsetGeonet,\
                  location = locationGeonet, dbase = gisdbdir)
    # gsetup initialization 
    gsetup.init(gisbase, gisdbdir, locationGeonet, mapsetGeonet)
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
    config = ConfigParser.RawConfigParser()
    config.read(os.path.join(os.path.dirname(
        os.path.dirname(
            inspect.stack()[0][1])),
                             'GeoFlood.cfg'))
    geofloodHomeDir = config.get('Section', 'geofloodhomedir')
    projectName = config.get('Section', 'projectname')
    DEM_name = config.get('Section', 'dem_name')
    #geofloodHomeDir = "H:\GeoFlood"
    #projectName = "Test_Stream"
    #DEM_name = "DEM"
    geofloodResultsDir = os.path.join(geofloodHomeDir, "Outputs",
                                      "GIS", projectName)
    Name_path = os.path.join(geofloodResultsDir, DEM_name)
    fdrfn = Name_path + '_fdr.tif'
    segshp = Name_path+ "_channelSegment.shp"
    segcatfn = Name_path + '_segmentCatchment.tif'
    segment_catchment_delineation(fdrfn, segshp, segcatfn)

if __name__ == '__main__':
    main()
