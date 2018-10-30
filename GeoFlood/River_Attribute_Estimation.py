import os
import numpy as np
from scipy import stats
from osgeo import gdal,ogr
import ConfigParser
import inspect


def river_attribute_estimation(segment_shp, segcatfn,
                               segcat_shp, burndemfn,
                               attribute_txt):
    rafile = open(attribute_txt,"w")
    driver = ogr.GetDriverByName("ESRI Shapefile")
    dataSource = driver.Open(segment_shp, 0)
    layer = dataSource.GetLayer()
    featureCount = layer.GetFeatureCount()
    rafile.write(str(featureCount)+"\n")
    raster = gdal.Open(burndemfn) 
    gt = raster.GetGeoTransform()
    rasterBand = raster.GetRasterBand(1)
    cat_raster = gdal.Open(segcatfn) 
    cat_rasterBand = cat_raster.GetRasterBand(1)
##    raster_arr = np.array(cat_rasterBand.ReadAsArray())
##    nodata = -32768
##    nodatamask = raster_arr == nodata
##    mask = cat_rasterBand.GetMaskBand().ReadAsArray()
    mask = cat_rasterBand.GetMaskBand()
    ds = driver.CreateDataSource(segcat_shp)
    cat_layer = ds.CreateLayer(segcat_shp)
    field = ogr.FieldDefn("HYDROID", ogr.OFTInteger)
    cat_layer.CreateField(field)
    dst_field = cat_layer.GetLayerDefn().GetFieldIndex("HYDROID")
    gdal.Polygonize(cat_rasterBand, mask, cat_layer, dst_field,
                    [], callback=None)
    ds.Destroy()
    ds = driver.Open(segcat_shp, 1)
    cat_layer = ds.GetLayer()
    cat_layer.CreateField(ogr.FieldDefn('AreaSqKm', ogr.OFTReal))
    for feat in cat_layer:
        geom = feat.GetGeometryRef()
        feat.SetField('AreaSqKm',float(geom.Area())/1000**2)
        cat_layer.SetFeature(feat)
        feat.Destroy()
    for feature in layer:
        geom = feature.GetGeometryRef()
        feat_id = feature.GetField('HYDROID')
        length = feature.GetField('Length')/1000
        point_geom_list = geom.GetPoints()
        mx = np.array([])
        my = np.array([])
        for i in range(len(point_geom_list)):
            mx = np.append(mx, point_geom_list[i][0])
            my = np.append(my, point_geom_list[i][1])
        px = ((mx - gt[0]) / gt[1]).astype(int)
        py = ((my - gt[3]) / gt[5]).astype(int)
        x_diff = np.diff(px)
        y_diff = np.diff(py)
        m_array = np.sqrt(x_diff**2 + y_diff**2)
        m_array = np.insert(m_array, 0, 0)
        m_array = np.cumsum(m_array)
        z_array = rasterBand.ReadAsArray()[py, px].flatten()
        slope = -stats.linregress(m_array, z_array)[0]
        cat_layer.SetAttributeFilter("HYDROID = "+str(feat_id))
        for feat in cat_layer:
            area = feat.GetField("AreaSqKm")
            feat.Destroy()
        feature.Destroy()
        rafile.write(str(feat_id)+" "+str(slope)+" "+str(length)+" "+str(area)+"\n")
    rafile.close()
    dataSource.Destroy()
    ds.Destroy()
    


def main():
    config = ConfigParser.RawConfigParser()
    config.read(os.path.join(os.path.dirname(
        os.path.dirname(
            inspect.stack()[0][1])),
                             'GeoFlood.cfg'))
    geofloodHomeDir = config.get('Section', 'geofloodhomedir')
    projectName = config.get('Section', 'projectname')
    #geofloodHomeDir = "H:\GeoFlood"
    #projectName = "Test_Stream"
    burn_option = 0
    geofloodResultsDir = os.path.join(geofloodHomeDir, "Outputs",
                                      "GIS", projectName)
    DEM_name = config.get('Section', 'dem_name')
    #DEM_name = "DEM"
    Name_path = os.path.join(geofloodResultsDir, DEM_name)
    segment_shp = Name_path + "_channelSegment.shp"
    segcatfn = Name_path + "_segmentCatchment.tif"
    segcat_shp = Name_path + "_segmentCatchment.shp"
    hydro_folder = os.path.join(geofloodHomeDir,
                                "Outputs", "Hydraulics",
                                projectName)
    if not os.path.exists(hydro_folder):
        os.mkdir(hydro_folder)
    attribute_txt = os.path.join(hydro_folder,
                                 DEM_name+"_River_Attribute.txt")
    burn_option = config.get('Section', 'burn_option')
    if burn_option == 1:
        burndemfn = Name_path + "_fdc.tif"
        river_attribute_estimation(segment_shp, segcatfn,
                                   segcat_shp, burndemfn,
                                   attribute_txt)
    else:
        demfn = os.path.join(geofloodHomeDir, "Inputs",
                             "GIS", projectName, DEM_name+".tif")
        river_attribute_estimation(segment_shp, segcatfn,
                                   segcat_shp, demfn,
                                   attribute_txt)


if __name__ == "__main__":
    main()
