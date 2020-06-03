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
    - [PROJECT_NAME]
  - Hydraulics
    - [PROJECT_NAME]
  - NWM
    - [PROJECT_NAME]
- Outputs
  - GIS
    - [PROJECT_NAME]
  - Hydraulics
    - [PROJECT_NAME]
  - Inundation
  - NWM
    - [PROJECT_NAME]
Place **my_dem.tif** into the *Inputs/GIS/[PROJECT_NAME]* directory that was just created.

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


### 5. GeoFlood Workflow
Navigate to the *GeoFlood* directory.

