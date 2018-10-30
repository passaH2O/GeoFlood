import os
import sys
import shutil
import subprocess
import ConfigParser
import inspect


def grass_controller(geofloodHomeDir):
    grass7bin = 'grass74'
    # grass7bin = 'grass72'
    if sys.platform.startswith('win'):
        # MS Windows
        grass7bin = r'C:\Program Files (x86)\GRASS GIS 7.4.0\grass74.bat'
        # grass7bin = r'C:\Program Files\GRASS GIS 7.2.1\grass72.bat'
        # uncomment when using standalone WinGRASS installer
        # grass7bin = r'C:\Program Files (x86)\GRASS GIS 7.2.0\grass72.bat'
        # this can be avoided if GRASS executable is added to PATH
    elif sys.platform == 'darwin':
        # Mac OS X
        # TODO: this have to be checked, maybe unix way is good enough
        grass7bin = '/Applications/GRASS/GRASS-7.2.app/'
    mswin = sys.platform.startswith('win')
    if mswin:
        gisdbdir = os.path.join(os.path.expanduser("~"), "Documents\grassdata")
    else:
        gisdbdir = os.path.join(os.path.expanduser("~"), "grassdata")
    locationGeonet = 'geonet'
    mapsetGeonet = 'geonetuser'
    if sys.platform.startswith("win"):
        import ctypes
        SEM_NOGPFAULTERRORBOX = 0x0002  # From MSDN
        ctypes.windll.kernel32.SetErrorMode(SEM_NOGPFAULTERRORBOX)
        CREATE_NO_WINDOW = 0x08000000    # From Windows API
        subprocess_flags = CREATE_NO_WINDOW
    else:
        subprocess_flags = 0
    subprocess_flags = 0
    startcmd = [grass7bin, os.path.join(gisdbdir, locationGeonet,
                                        mapsetGeonet), '--exec',
                os.path.join(geofloodHomeDir, "Tools",
                             "GeoFlood", "Grass_Delineation.py")]
##    startcmd = ['python', os.path.join(os.path.dirname(__file__),
##                                       "Grass_Delineation.py")]
    p = subprocess.Popen(startcmd, shell=True,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         creationflags=subprocess_flags)
    out, err = p.communicate()
    print out, err


def main():
    config = ConfigParser.RawConfigParser()
    config.read(os.path.join(os.path.dirname(
        os.path.dirname(
            inspect.stack()[0][1])),
                             'GeoFlood.cfg'))
    geofloodHomeDir = config.get('Section', 'geofloodhomedir')
    grass_controller(geofloodHomeDir)

if __name__ == '__main__':
    main()
