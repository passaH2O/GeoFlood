# GeoFlood
Flood mapping program based on high-resolution terrain analyses.

# Configuration 
Navigate to the *GeoNet* directory

Start with the 'pygeonet_prepare.py' script. This will create the necessary file structure and configuration file to run GeoNet/GeoFlood. 
You will need to specify a 'Project Name' and 'DEM Name' that will be used for the rest of the workflow.

For example, if I wanted to create a project titled 'my_project' with a dem name of 'my_dem', execute
```
python pygeonet_prepare.py my_project my_dem
```

Resulting File Structure:
- GeoNet
- GeoFlood
- Inputs
  - GIS
    - my_project
  - Hydraulics
    - my_project
  - NWM
    - my_project
- Outputs
  - GIS
    - my_project
  - Hydraulics
    - my_project
  - Inundation
  - NWM
    - my_project

Place **my_dem.tif** into the *Inputs/GIS/my_project* directory that was just created.

# GeoNet Workflow
### 1. DEM smoothing
```
python pygeonet_nonlinear_filter.py
```
To change the number of smoothing iterations (currently set at 50), edit the 'nFilterIterations' variable in the **pygeonet_defaults.py** script

### 2. Slope and Curvature
```
python pygeonet_slope_curvature.py
```
A geometric curvature calculation is the default, but can be changed to a laplacian curvature by changing the 'curvatureCalcMethod' in the **pygeonet_defaults.py** script from *geometric* to *laplacian*.

### 3. GRASS GIS





### 4. Flow Accumulation and Curvature Skeleton
```
python pygeonet_skeleton_definition.py
```
The flow accumulation threshold used in this script can be adjusted by changing the value set to the 'flowThresholdForSkeleton' variable in the **pygeonet_defaults.py**
- Decreasing the threshold increases the density of the network, i.e. more pixels classified as likely channels/reaches.
- Increasing the threshold decreases the density of the extracted network.


# GeoFlood Workflow
GeoFlood was designed to work with NHD MR flowlines as those are the flowlines used in the National Water Model. Find NHD MR vector data here:
- https://www.arcgis.com/home/webmap/viewer.html?webmap=9766a82973b34f18b43dafa20c5ef535&extent=-140.4631,21.8744,-48.5295,57.4761
or
- https://viewer.nationalmap.gov/basic/?basemap=b1&category=nhd&title=NHD%20View

From these downloads, you specifically need the shapefiles of NHD MR Flowlines and their associated catchments. To do this, navigate to the NFIE folder you downloaded within any GIS software (QGIS,ArcGIS Pro, ArcMap,...) and upload the flowline and catchments of interest. The shapefiles of interest can then be extracted.

**Place the extracted flowline and catchment shapefiles into the *Inputs/Hydraulics/my_project* folder**

### 5. Network Node Reading
`cd ../GeoFlood`

`python Network_Node_Reading.py`

This script will output a csv containing the start and end points of the flowlines of interest.

### 6. Negative Height Above Nearest Drainage
`python Relative_Height_Estimation.py`

Returns a binary raster/array with values of 1 given to pixels at a lower elevation than the elevation associated with NHD MR Flowline pixels. A value of zero is given to all other pixels in the image, i.e. pixels at a higher elevation than the NHD MR Flowlines.

### 7. Network Extraction
`python Network_Extraction.py`

Returns a shapefile of the extracted network, a binary raster of the "burned in" extracted network, and a cost raster. In this context, "burned in" does not mean modifying the elevations of the input rater, but rather giving a value of 1 to pixels representing the extracted network and 0 to all other pixels.

**Note: If the input DEM is > 1.5 GB, the input arrays to this script will be batch processed for memory management purposes.**

# TauDEM Functions
Please refer to the TauDEM user guide for more specific instructions and descriptions about their entire suite of products. 

TauDEM User Guide: https://hydrology.usu.edu/taudem/taudem5/TauDEM53GettingStartedGuide.pdfage

For the GeoNet/GeoFlood workflow the following functions are used: 
- PitRemove
- D-Infinity flow directions
- D-Infitinity flow accumulation
- HAND (Height Above Nearest Drain)
- Hydraulic property base table
- Inunmap

The following commands were all ran from the command line/anaconda prompt.

### 8. Pit Filling
`mpiexec -n [integer value representing the number of proceses to use] *path/to/TauDEM/pitremove*-z *path/to/input/dem.tif* -fel *path/to/output/GIS/dem_fel.tif*`

### 9. D-Infinity Flow Direction:
`mpiexec -n [integer value representing the number of proceses to use] *path/to/TauDEM/dinfflowdir* - fel *path/to/outputs/GIS/dem_fel.tif* -ang *path/to/outputs/GIS/dem_ang.tif* -slp *path/to/outputs/GIS/dem_slp.tif*`

Both '_ang' and '_slp' are outputs of this command.

### 10. D-Infinity Flow Accumulation
`mpiexec -n [integer value representing the number of proceses to use] *path/to/TauDEM/areadinf* - ang *path/to/outputs/GIS/dem_ang.tif* -sca *path/to/outputs/GIS/dem_sca.tif*`

### 11. Height Above Nearest Drainage
`mpiexec -n [integer value representing the number of proceses to use] *path/to/TauDEM/dinfdistdown* - ang *path/to/outputs/GIS/dem_ang.tif* -fel *path/to/outputs/GIS/dem_fel.tif* -slp *path/to/outputs/GIS/dem_slp.tif* -src *path/to/outputs/GIS/dem_path.tif* -dd *path/to/outputs/GIS/dem_hand.tif* -m ave v`

# Back to GeoFlood

### 12. Segmenting Extracted Network
`python Streamline_Segmentation.py`

Currently set at 1000m.

### 13. 

