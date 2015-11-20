#!/usr/bin/python
# -*- coding: utf-8 -*-
#Check with lv03-Tile (test overlapping )

from osgeo import gdal
from osgeo import ogr, osr
import os
#import urllib2
import json
import subprocess
import logging
import requests


year = "2014"
year_short = "14"
theme = "dtm"
gsd = "5.00"
aufloesung="500cm"
colorisation = "gray"
gsd_original ="50cm"
if colorisation is "rgb":
    photometric_color="YCBCR"
if colorisation is "gray":
    photometric_color="MINISBLACK"

##Settings for RestService
#proxy = urllib2.ProxyHandler({'http': 'http://barpastu:qwertz123$@proxy2.so.ch:8080'})
#auth = urllib2.HTTPBasicAuthHandler()
#opener = urllib2.build_opener(proxy, auth, urllib2.HTTPHandler)
#urllib2.install_opener(opener)

#Logger for warnings and errors
logger_error = logging.getLogger('brw_error')
handler_error = logging.FileHandler('log_brw_error_lidar.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler_error.setFormatter(formatter)
logger_error.addHandler(handler_error) 
logger_error.setLevel(logging.WARNING)

#Logger for notices
logger_notice = logging.getLogger('brw')
handler_notice = logging.FileHandler('log_brw_lidar.log')
handler_notice.setFormatter(formatter)
logger_notice.addHandler(handler_notice) 
logger_notice.setLevel(logging.INFO)




#Start calculations
logger_notice.info("Start Lidar " + theme + " " + year + " " + gsd)


##Settings 

#resampling-method
method = 'lanczos'

#path to the data on the old storage
path_old_location= "/home/barpastu/Geodaten/LV03/lidar" + year + "/" + theme

#path to the data on the new storage
path_new_location= "/home/barpastu/Geodaten/LV95/lidar/" + year + "/" + theme

#path to the data of gsd 50 cm on the new storage
path_lv95_50 = path_new_location + "/" + colorisation + "/" + gsd_original

#path to the data on the new storage (LV03)
path_lv03 =  path_old_location  #+ "/"+ colorisation + "/" + aufloesung 

#path to the data on the new storage (LV95)
path_lv95 = path_new_location + "/"+ colorisation + "/" + aufloesung 

#Filename of the vrt
orthofilename = theme + "_5m_"+year

#path of the vrt
vrt_95 = path_lv95 + "/ohne_overviews/" +orthofilename+".vrt"

height_extract = 500
vrt_exists = False


#Create Folders
if not os.path.exists(path_lv95):
    os.makedirs(path_lv95)
if not os.path.exists(path_lv95 + "/difference"):
    os.makedirs(path_lv95 + "/difference")
if not os.path.exists(path_lv95 + "/ohne_overviews"):
    os.makedirs(path_lv95 + "/ohne_overviews")
if not os.path.exists(path_lv03 + "/working/"):
    os.makedirs(path_lv03 + "/working/")




ogr.UseExceptions() 



#Create Tileindex based on vrt LV95 (50_cm) --> only one tile
cmd = "gdaltindex -write_absolute_path " + path_lv03 + "/" + orthofilename + ".shp " 
cmd += path_lv95 + "/ausschnitt_dtm_5m_2014_5m.tif"
os.system(cmd)
print(cmd)


#Shape-File with tile division
shp = ogr.Open(path_lv03 + "/" + orthofilename + ".shp")
layer = shp.GetLayer(0)

# Do for each tile
for feature in layer:
    infileName = feature.GetField('location')
    print infileName
    geom = feature.GetGeometryRef()
    env = geom.GetEnvelope()

    minX = int(env[0] + 0.001 + 2000000)
    minY = int(env[2] + 0.001 + 1000000)
    maxX = int(env[1] + 0.001 + 2000000)
    maxY = int(env[3] + 0.001 + 1000000)

    middleX = (int(env[0] + 0.001)+int(env[1] + 0.001 ))/2
    middleY = (int(env[2] + 0.001)+int(env[3] + 0.001 ))/2

    
    outfileName_jpeg = orthofilename + "_5m.tif" 
    infileNameFile_jpeg = outfileName_jpeg


    #Ausschnitt generieren LV03
    cmd = " gdalwarp -co PHOTOMETRIC=" + photometric_color + " -co TILED=YES -co PROFILE=GeoTIFF -tr " + gsd + " " + gsd
    cmd += " -te " + str(minX) + " " + str(minY) + " " 
    cmd += str(maxX) + " " + str(maxY) + " "
    cmd +=os.path.join(path_lv03, "dtm2014_5m.tif") + " " 
    cmd +=os.path.join(path_lv03, "working", "ausschnitt_"+infileNameFile_jpeg)
    os.system(cmd)

    #Calculate Difference
    cmd = "gdal_calc.py -A " 
    cmd += os.path.join(path_lv03,"working", "ausschnitt_"+infileNameFile_jpeg) + " -B " 
    cmd += os.path.join(path_lv95, "ausschnitt_dtm_5m_2014_5m.tif")+ " " 
    cmd += "--outfile=" +os.path.join(path_lv95,"difference","orig_"+outfileName_jpeg)
    cmd += " --calc=\"A-B\""
    os.system(cmd)

    cmd = "gdal_calc.py -A "+os.path.join(path_lv95,"difference","orig_"+outfileName_jpeg) + " "
    cmd += "--outfile=" + os.path.join(path_lv95,"difference",outfileName_jpeg) + " "
    cmd += "--calc=\"(absolute(A)<=0.1)*0 + (absolute(A)>0.1)*1\" --NoDataValue=10"
    os.system(cmd)

    cmd = "convert "+os.path.join(path_lv95,"difference",outfileName_jpeg)
    cmd += " -format \"%[fx:mean*100]\" info:"
    cmd = cmd.split(" ")
    false_pixel_percent=subprocess.check_output(cmd)
    false_pixel_percent=false_pixel_percent.replace('\n','')
    false_pixel_percent=false_pixel_percent.replace('\"','')
    #print repr(false_pixel_percent)
    logger_notice.info("Anteil falscher Pixelwerte: " +false_pixel_percent )


    if float(false_pixel_percent)>=1:
        logger_error.error(os.path.join(path_lv95,"difference",outfileName_jpeg)+" weist einen Anteil von mehr als 1% falscher Pixelwerte auf. Folgender Anteil: "+false_pixel_percent)
    else :
        cmd = "rm " + os.path.join(path_lv03, "ausschnitt_"+infileNameFile_jpeg)
        os.system(cmd)
        cmd = "rm " + os.path.join(path_lv95, "ausschnitt_"+outfileName_jpeg)
        os.system(cmd)
        cmd = "rm " + os.path.join(path_lv95,"difference","orig_"+outfileName_jpeg)
        os.system(cmd)
        cmd = "rm " + os.path.join(path_lv95,"difference",outfileName_jpeg)
        os.system(cmd)
cmd = "rm -r " + os.path.join(path_lv95, "ohne_overviews")
os.system(cmd)
cmd = "rm -r " + os.path.join(path_lv03, "working")
os.system(cmd)
#cmd = "rm " + path_lv03 + "/" + orthofilename + ".shp " 
cmd += path_lv03 + "/" + orthofilename + ".vrt " + path_lv03 + "/" + orthofilename + ".shx " 
cmd += path_lv03 + "/" + orthofilename + ".prj " + path_lv03 + "/" + orthofilename + ".dbf "
#os.system(cmd)

logger_notice.info("Ende")

