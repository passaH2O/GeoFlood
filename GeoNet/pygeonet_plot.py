import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
import pygeonet_defaults as defaults


def raster_plot(Array, title):
    if not hasattr(defaults, 'figureNumber'):
        defaults.figureNumber = 0
    defaults.figureNumber = defaults.figureNumber + 1
    plt.figure(defaults.figureNumber)
    plt.imshow(Array, cmap=cm.coolwarm)
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.title(title)
    plt.colorbar()
    if defaults.doPlot==1:
        plt.show()
        #If instead of showing the figure you prefer to save directly, use the three lines below instead
        #png_file = '{0}.png'.format(title)
        #plt.savefig(png_file)
        #plt.close()


def raster_point_plot(Array, PointsList, title, color=cm.coolwarm, point_style='go'):
    if not hasattr(defaults, 'figureNumber'):
        defaults.figureNumber = 0
    defaults.figureNumber = defaults.figureNumber + 1
    plt.figure(defaults.figureNumber)
    plt.imshow(Array, cmap=color)
    plt.plot(PointsList[1],PointsList[0],point_style)
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.title(title)
    plt.colorbar()
    if defaults.doPlot==1:
        plt.show()
        #If instead of showing the figure you prefer to save directly, use the three lines below instead
        #png_file = '{0}.png'.format(title)
        #plt.savefig(png_file)
        #plt.close()

def geodesic_contour_plot(geodesicDistanceArray, title):
    if not hasattr(defaults, 'figureNumber'):
        defaults.figureNumber = 0
    defaults.figureNumber = defaults.figureNumber + 1
    plt.figure(defaults.figureNumber)
    plt.imshow(np.log10(geodesicDistanceArray),cmap=cm.coolwarm)
    plt.contour(geodesicDistanceArray,140,cmap=cm.coolwarm)
    plt.title(title)
    plt.colorbar()
    if defaults.doPlot==1:
        plt.show()
        #If instead of showing the figure you prefer to save directly, use the three lines below instead
        #png_file = '{0}.png'.format(title)
        #plt.savefig(png_file)
        #plt.close()
        
def channel_plot(flowDirectionsArray,geodesicPathsCellList,
                 xx,yy,title,color=cm.coolwarm,
                 point_style='go',line_style='k-'):
    if not hasattr(defaults, 'figureNumber'):
        defaults.figureNumber = 0
    defaults.figureNumber = defaults.figureNumber + 1
    plt.figure(defaults.figureNumber)
    plt.imshow(flowDirectionsArray,cmap=color)
    for pp in range(0,len(geodesicPathsCellList)):
        plt.plot(geodesicPathsCellList[pp][1,:],geodesicPathsCellList[pp][0,:],line_style)
    plt.plot(xx,yy,point_style)
    plt.title(title)
    plt.colorbar()
    if defaults.doPlot==1:
        plt.show()
        #If instead of showing the figure you prefer to save directly, use the three lines below instead
        #png_file = '{0}.png'.format(title)
        #plt.savefig(png_file)
        #plt.close()

