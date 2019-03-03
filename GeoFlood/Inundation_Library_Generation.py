import os
import numpy as np
import ConfigParser
import inspect
from osgeo import ogr, osr, gdal, gdal_array


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
    geofloodResultsDir = os.path.join(geofloodHomeDir, "Outputs",
                                      "GIS", projectName)
    DEM_name = config.get('Section', 'dem_name')
    #DEM_name = "DEM"
    Name_path = os.path.join(geofloodResultsDir, DEM_name)
    hand_raster = Name_path+ "_hand.tif"
    ds = gdal.Open(hand_raster)
    srs = osr.SpatialReference(wkt = ds.GetProjection())
    band = ds.GetRasterBand(1)
    hand_arr = band.ReadAsArray()
    nodata = band.GetNoDataValue()
    segcatchment_tif = Name_path+"_segmentCatchment.tif"
    segcat_ds = gdal.Open(segcatchment_tif)
    segcat_band = segcat_ds.GetRasterBand(1)
    segcat_arr = segcat_band.ReadAsArray()
    network_table = Name_path+"_networkMapping.csv"
    hydroids = np.loadtxt(network_table, dtype=int, skiprows = 1,
                          delimiter=',', usecols=(0,))
##    segcatchment_shp = Name_path+ "_segmentCatchment.shp"
##    driver = ogr.GetDriverByName("ESRI Shapefile")
##    #spatialRef.MorphToESRI()
##    srsfile = open(segcatchment_shp[:-4]+".prj", 'w')
##    srsfile.write(srs.ExportToWkt())
##    srsfile.close()
    stage_txt = os.path.join(geofloodHomeDir, "Inputs",
                             "Hydraulics", projectName,
                             "stage.txt")
    stages = np.loadtxt(stage_txt, skiprows = 1)
    fplibrary_folder = os.path.join(geofloodHomeDir, "Outputs",
                                    "InundationLibrary", projectName)
    if not os.path.exists(fplibrary_folder):
        os.mkdir(fplibrary_folder)
    Name_path = os.path.join(fplibrary_folder, DEM_name)
    driver = ogr.GetDriverByName("ESRI Shapefile")
    for i in range(len(stages)):
        stage = stages[i]
        data = np.where((hand_arr<=stage) & (hand_arr >= 0),1,0)
        fp_raster = Name_path+"_fpzone"+str(i)+".tif"
        gdal_array.SaveArray(data.astype("int8"),
                             fp_raster, "GTIFF", ds)
        fp_vector = Name_path+"_fpzone"+str(i) + ".shp"
        dst_ds = driver.CreateDataSource(fp_vector)
        dst_layer = dst_ds.CreateLayer(fp_vector, srs)
        tmpds = gdal.Open(fp_raster)
        tmpband = tmpds.GetRasterBand(1)
        # tmpband.SetNoDataValue(0)
        gdal.Polygonize(tmpband, tmpband, dst_layer, -1, ["8CONNECTED"],
                        callback=None)
        dst_ds.Destroy()
    for hydroid in hydroids:
        catch_fplibrary_folder = os.path.join(fplibrary_folder,
                                              "Catchment_"+str(hydroid))
        if not os.path.exists(catch_fplibrary_folder):
            os.mkdir(catch_fplibrary_folder)
        for i in range(len(stages)):
            stage = stages[i]
            catch_stage_fp_tif = os.path.join(catch_fplibrary_folder,
                                              'fp_'+str(i)+'.tif')
            catch_stage_fp_shp = os.path.join(catch_fplibrary_folder,
                                              'fp_'+str(i)+'.shp')
            data = np.where((hand_arr<=stage) & (hand_arr >= 0) & \
                            (segcat_arr == hydroid),1,0)
            gdal_array.SaveArray(data.astype("int8"),
                                 catch_stage_fp_tif,
                                 "GTIFF", ds)
            dst_ds = driver.CreateDataSource(catch_stage_fp_shp)
            dst_layer = dst_ds.CreateLayer(catch_stage_fp_shp, srs)
            tmpds = gdal.Open(catch_stage_fp_tif)
            tmpband = tmpds.GetRasterBand(1)
##            tmpband.SetNoDataValue(0)
            gdal.Polygonize(tmpband, tmpband, dst_layer,
                            -1, ["8CONNECTED"], callback=None)
            dst_ds.Destroy()
##            srsfile = open(catch_stage_fp_shp[:-4]+".prj", 'w')
##            srsfile.write(srs.ExportToWkt())
##            srsfile.close()

    
##    for stage in range(1,5):
##        dataSource = driver.Open(segcatchment_shp, 0)
##        layer = dataSource.GetLayer()
##        data = np.where((hand_arr<=stage) & (hand_arr >= 0),1,0)
##        fp_raster = Name_path+"_fp"+str(stage)+".tif"
##        gdal_array.SaveArray(data.astype("int8"),
##                             fp_raster,
##                             "GTIFF", ds)
##        fp_vector = Name_path+"_fp"+str(stage) + ".shp"
##        dst_ds = driver.CreateDataSource(fp_vector)
##        dst_layer = dst_ds.CreateLayer(fp_vector, srs)
##        tmpds = gdal.Open(fp_raster)
##        tmpband = tmpds.GetRasterBand(1)
##        tmpband.SetNoDataValue(0)
##        gdal.Polygonize(tmpband, tmpband, dst_layer, -1, ["8CONNECTED"], callback=None)
##        dst_ds.Destroy()
##        srsfile = open(fp_vector[:-4]+".prj", 'w')
##        srsfile.write(srs.ExportToWkt())
##        srsfile.close()
##        for feature1 in layer:
##            geom1 = feature1.GetGeometryRef()
##            print geom1.GetArea()
##            attribute1 = feature1.GetField('HYDROID')
##            catch_fplibrary_folder = os.path.join(fplibrary_folder,
##                                                  "Catchment_"+str(attribute1))
##            if not os.path.exists(catch_fplibrary_folder):
##                os.mkdir(catch_fplibrary_folder)
##            catch_stage_fp_shp = os.path.join(catch_fplibrary_folder,
##                                                'fp_'+str(stage)+'.shp')
##            catch_stage_fp_ds = driver.CreateDataSource(catch_stage_fp_shp)
##            catch_stage_fp_layer = catch_stage_fp_ds.CreateLayer(
##                catch_stage_fp_shp, srs, geom_type=ogr.wkbPolygon)
##            #catch_stage_fp_layer.CreateField(ogr.FieldDefn("HYDROID", ogr.OFTInteger))
##            tmpdataSource = driver.Open(fp_vector,0)
##            dst_layer = tmpdataSource.GetLayer()
##            for feature2 in dst_layer:
##                geom2 = feature2.GetGeometryRef()
##                intersection = geom2.Intersection(geom1)
##                max_area = 0
##                max_g = None
##                for i in range(0, intersection.GetGeometryCount()):
##                    g = intersection.GetGeometryRef(i)
##                    if g.GetGeometryName() == "POLYGON":
##                        if g.GetArea() > max_area:
##                            max_area = g.GetArea()
##                            max_g = g
##                dstfeature = ogr.Feature(catch_stage_fp_layer.GetLayerDefn())
##                dstfeature.SetGeometry(max_g)
##                catch_stage_fp_layer.CreateFeature(dstfeature)
##                dstfeature.Destroy()
##            tmpdataSource.Destroy()
##            catch_stage_fp_ds.Destroy()
##        dataSource.Destroy()


if __name__ == "__main__":
    main()
