#!/usr/bin/python
# -*- coding: utf-8 -*-
#Check with lv03-Tile (test overlapping )

from osgeo import gdal
from osgeo import ogr, osr
import os
import requests
import json
import subprocess
import logging
#import urllib2


year = "2007"
year_short = "07"
gsd = "0.125"
aufloesung="12_5cm"
colorisation = "rgb"


##Settings for RestService
#proxy = urllib2.ProxyHandler({'http': 'http://barpastu:qwertz123$@proxy2.so.ch:8080'})
#auth = urllib2.HTTPBasicAuthHandler()
#opener = urllib2.build_opener(proxy, auth, urllib2.HTTPHandler)
#urllib2.install_opener(opener)


#Logger for warnings and errors
logger_error = logging.getLogger('brw_error')
handler_error = logging.FileHandler('log_brw_error_2007.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler_error.setFormatter(formatter)
logger_error.addHandler(handler_error) 
logger_error.setLevel(logging.WARNING)

#Logger for notices
logger_notice = logging.getLogger('brw')
handler_notice = logging.FileHandler('log_brw_2007.log')
handler_notice.setFormatter(formatter)
logger_notice.addHandler(handler_notice) 
logger_notice.setLevel(logging.INFO)




#Start calculations
logger_notice.info("Start " + year)


##Settings 

#resampling-methode
method = 'lanczos'

#path to LV03-Data
path_old_location = "/home/barpastu/Geodaten/LV03/ortho" + year_short + "/" + aufloesung

#path to LV95-Data (without colorisation and resolution)
path_new_location="/home/barpastu/Geodaten/LV95/orthofoto/" + year

#path to LV03-Data
path_lv03 = path_old_location 

#path to LV95-Data
path_lv95 = path_new_location + "/"+ colorisation + "/" + aufloesung 

#Filename of vrt
orthofilename = "ortho"+year

#path to lv03-vrt
vrt = path_lv03 + "/" + orthofilename+".vrt"

#path to lv95-vrt
vrt_95 = path_lv95 + "/ohne_overviews/" +orthofilename+".vrt"

#settings for check
vrt_exists = False




#Create Tileindex for lv03
cmd = "gdaltindex -write_absolute_path " + path_lv03 + "/" + orthofilename + ".shp " 
cmd += path_lv03 + "/working/*.tif"
os.system(cmd)


#Shape-File with tile division
shp = ogr.Open(path_lv03 + "/" + orthofilename + ".shp")
layer = shp.GetLayer(0)



# Do a check for each tile
for feature in layer:
    infileName = feature.GetField('location')
    geom = feature.GetGeometryRef()
    env = geom.GetEnvelope()

    minX = int(env[0] + 0.001 )
    minY = int(env[2] + 0.001 )
    maxX = int(env[1] + 0.001 )
    maxY = int(env[3] + 0.001 )

    middleX = (int(minX + 0.001)+int(maxX + 0.001 ))/2
    middleY = (int(minY + 0.001)+int(maxY + 0.001 ))/2
    
    infileNameFile_jpeg = str(minX)[0:3] + str(minY)[0:3] + "_"+aufloesung+".tif"   
    outfileName_jpeg = "2" + str(minX)[0:3] + "1" + str(minY)[0:3] + "_"+aufloesung+".tif" 


    # generate Overviews 
    cmd = "gdaladdo -r nearest --config COMPRESS_OVERVIEW DEFLATE "
    cmd += "--config PHOTOMETRIC_OVERVIEW YCBCR "
    cmd += "--config GDAL_TIFF_OVR_BLOCKSIZE 512 " 
    cmd += path_lv95 + "/" + outfileName_jpeg + " 2 4 8 16 32 64 128"
    os.system(cmd) 




    
cmd = "rm " + path_lv03 + "/" + orthofilename + ".shp " 
cmd += path_lv03 + "/" + orthofilename + ".vrt " + path_lv03 + "/" + orthofilename + ".shx " 
cmd += path_lv03 + "/" + orthofilename + ".prj " + path_lv03 + "/" + orthofilename + ".dbf "
#os.system(cmd)

logger_notice.info("Ende")

