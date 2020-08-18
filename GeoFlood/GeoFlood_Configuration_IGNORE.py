import ConfigParser
import os
import sys
import inspect


config = ConfigParser.RawConfigParser()
config.add_section('Section')
geofloodHomeDir = str(sys.argv[1])
config.set('Section', 'geofloodHomeDir', geofloodHomeDir)
#config.set('Section', 'geofloodHomeDir', "H:\GeoFlood")
config.set('Section', 'projectName', str(sys.argv[2]))
#config.set('Section', 'projectName', "Test_Stream")
config.set('Section', 'DEM_name', str(sys.argv[3]))
#config.set('Section', 'DEM_name', "DEM")
config.set('Section', 'product_type', str(sys.argv[4]))
#config.set('Section', 'product_type', "short_range")
config.set('Section', 'date', str(sys.argv[5]))
#config.set('Section', 'date', "180902")
config.set('Section', 'nwmfn', str(sys.argv[6]))
##config.set('Section', 'nwmfn', "nwm.t02z.short_range." +
##           "channel_rt.f001.conus.nc")
config.set('Section', 'burn_option', str(sys.argv[7]))


# Writing our configuration file to 'example.cfg'
with open(os.path.join(os.path.dirname(os.path.dirname(
    inspect.stack()[0][1])),
                       'GeoFlood.cfg'),
          'wb') as configfile:
    config.write(configfile)
