import gdal, osr
from osgeo import ogr
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pygeonet_rasterio import *

def raster2array(rasterfn):

    raster = gdal.Open(rasterfn)
    band = raster.GetRasterBand(1)
    array = band.ReadAsArray()
    return array


def cdf_plot(sorteddd, p, dd_80):

    width = 10
    fig_size = [width / 1.61803398875, width / 1.61803398875]
    plt.rc('font',family='Arial')
    fig, ax = plt.subplots(figsize=fig_size)
    ax.plot(sorteddd, p, 'k-', lw=2)
    ax.plot([0,dd_80], [0.8,0.8], 'r--',lw=1.5)
    ax.plot([dd_80,dd_80], [0,0.8], 'r--',lw=1.5)
    ax.plot([dd_80],[0.8],marker='o',markerfacecolor='r',
            linestyle='', ms=8, markeredgecolor='k', color='r', clip_on=False)
    ax.annotate("Threshold distance corresponding \nto 80 percentile: "+"{:.0f}".format(dd_80)+" meters",
                (dd_80*1.1,0.8),fontsize=18)
    plt.xlabel('Distance to stream (m)', fontsize=24)
    plt.ylabel('Cumulative Probability', fontsize=24)
##    plt.xticks(np.linspace(0,0.4,num=5),fontsize=18)
    plt.yticks(np.linspace(0,1,num=5),fontsize=18)
    ax.set_xlim(0,)
    ax.set_ylim(0,1)
    ax.margins(0.1, 0.1)
    fig.tight_layout()  # Removes some of the margin around the graph
    fig.subplots_adjust(top=0.85, right=0.85)
    fig.patch.set_facecolor('none')
    output_file = "Distance_Distribution"
    png_file = '{0}.png'.format(output_file)
    plt.savefig(png_file, facecolor=fig.get_facecolor())
    plt.close()


def main():
    outfilepath = Parameters.geonetResultsDir
    DEM_name = Parameters.demFileName.split('.')[0]
    ddfn = DEM_name + '_dd.tif'
    ddfn = os.path.join(outfilepath, ddfn)
    ddArray = raster2array(ddfn)
    ddArray = ddArray.astype(float)
    ddArray[np.where(ddArray<0)]=np.nan
    ddArray = ddArray[~np.isnan(ddArray)].flatten()
    sorteddd = np.sort(ddArray)
    p = 1. * np.arange(len(ddArray))/(len(ddArray) - 1)
    dd_80 = sorteddd[np.where(abs(p-0.8)<0.00001)][0]
    cdf_plot(sorteddd, p, dd_80)
    

    
    
if __name__ == "__main__":
    main()
