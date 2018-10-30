@echo off
set HomeDir="C:\GeoFlood"
set projectName="Test_Stream"
set DEM_name="DEM"
set product_type="short_range"
set date="180902"
set nwmfn="nwm.t02z.short_range.channel_rt.f001.conus.nc"
set burn_option=0
python .\GeoFlood\GeoFlood_Configuration.py %HomeDir% %projectName% %DEM_name% %product_type% %date% %nwmfn% %burn_option%
python .\GeoNet\pygeonet_nonlinear_filter.py
python .\GeoNet\pygeonet_slope_curvature.py
python .\GeoNet\pygeonet_flow_accumulation.py
python .\GeoNet\pygeonet_skeleton_definition.py
python .\GeoFlood\Network_Node_Reading.py
python .\GeoFlood\Network_Extraction.py
python .\GeoFlood\Streamline_Segmentation.py
python .\GeoFlood\Segment_Catchment_Delineation.py
python .\GeoFlood\River_Attribute_Estimation.py
python .\GeoFlood\Network_Mapping.py
mpiexec -n 4 .\TauDEM\pitremove -z ..\Inputs\GIS\\%projectName%\\%DEM_name%.tif -fel ..\\Outputs\GIS\\%projectName%\\%DEM_name%_fel.tif
mpiexec -n 4 .\TauDEM\dinfflowdir -fel ..\Outputs\GIS\\%projectName%\\%DEM_name%_fel.tif -ang ..\Outputs\GIS\\%projectName%\\%DEM_name%_ang.tif -slp ..\Outputs\GIS\\%projectName%\\%DEM_name%_slp.tif
mpiexec -n 4 .\TauDEM\dinfdistdown -fel ..\Outputs\GIS\\%projectName%\\%DEM_name%_fel.tif -ang ..\Outputs\GIS\\%projectName%\\%DEM_name%_ang.tif -src ..\Outputs\GIS\\%projectName%\\%DEM_name%_path.tif -dd ..\Outputs\GIS\\%projectName%\\%DEM_name%_hand.tif -m ave v
mpiexec -n 4 .\TauDEM\catchhydrogeo -hand ..\Outputs\GIS\\%projectName%\\%DEM_name%_hand.tif -catch ..\Outputs\GIS\\%projectName%\\%DEM_name%_segmentCatchment.tif -catchlist ..\Outputs\Hydraulics\\%projectName%\\%DEM_name%_River_Attribute.txt -slp ..\Outputs\GIS\\%projectName%\\%DEM_name%_slp.tif -h ..\Inputs\Hydraulics\\%projectName%\\stage.txt -table ..\Outputs\Hydraulics\\%projectName%\\hydroprop-basetable.csv
python .\GeoFlood\Hydraulic_Property_Postprocess.py
python .\GeoFlood\Forecast_Table.py
mpiexec -n 4 .\TauDEM\inunmap -hand ..\Outputs\GIS\\%projectName%\\%DEM_name%_hand.tif -catch ..\Outputs\GIS\\%projectName%\\%DEM_name%_segmentCatchment.tif -forecast ..\Outputs\NWM\\%product_type%\\%date%\\%nwmfn% -mapfile ..\Outputs\Inundation\\%product_type%\\%date%\\%DEM_name%_%nwmfn%_inunmap.tif