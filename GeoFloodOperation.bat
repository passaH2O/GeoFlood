@echo off
set HomeDir="C:\GeoFlood"
set projectName="Test_Stream"
set DEM_name="DEM"
set product_type="short_range"
set date="180902"
set nwmfn="nwm.t02z.short_range.channel_rt.f001.conus.nc"
set burn_option=0
python .\GeoFlood\GeoFlood_Configuration.py %HomeDir% %projectName% %DEM_name% %product_type% %date% %nwmfn% %burn_option%
python .\GeoFlood\Forecast_Table.py
mpiexec -n 4 .\TauDEM\inunmap -hand ..\Outputs\GIS\\%projectName%\\%DEM_name%_hand.tif -catch ..\Outputs\GIS\\%projectName%\\%DEM_name%_segmentCatchment.tif -forecast ..\Outputs\NWM\\%product_type%\\%date%\\%nwmfn% -mapfile ..\Outputs\Inundation\\%product_type%\\%date%\\%DEM_name%_%nwmfn%_inunmap.tif